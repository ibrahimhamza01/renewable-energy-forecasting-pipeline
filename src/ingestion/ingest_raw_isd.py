# src/ingestion/ingest_raw_isd.py

"""
Layer 5 Part A: Raw NOAA ISD ingestion to bronze.

Reads raw NOAA ISD CSV files from S3, preserves raw columns, adds ingestion
metadata, compacts output, and writes bronze Parquet to the active user's S3
bucket.

This script does NOT parse or clean encoded fields. That happens in silver.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from typing import Iterable

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F

from src.common.config import config
from src.common.paths import Paths
from src.common.spark_utils import get_spark_session
from src.storage.repartition_compaction import compact_for_bronze
from src.storage.write_bronze import write_bronze


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest raw NOAA ISD CSV files and write bronze Parquet."
    )

    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        required=True,
        help="Years to ingest. Example: --years 2018 2019 2020",
    )

    parser.add_argument(
        "--states",
        nargs="+",
        required=True,
        help="State codes to ingest. Example: --states CA TX MN FL",
    )

    parser.add_argument(
        "--station-master-path",
        required=True,
        help="Path to station master CSV or Parquet.",
    )

    parser.add_argument(
        "--max-stations",
        type=int,
        default=None,
        help="Optional station cap for test runs.",
    )

    parser.add_argument(
        "--target-files-per-year",
        type=int,
        default=8,
        help="Approximate number of bronze output files per year.",
    )

    parser.add_argument(
        "--mode",
        default="overwrite",
        choices=["overwrite", "append"],
        help="Write mode for bronze output.",
    )

    return parser.parse_args()


def load_station_master(
    spark: SparkSession,
    station_master_path: str,
    states: Iterable[str],
    max_stations: int | None = None,
) -> DataFrame:
    path_lower = station_master_path.lower()

    if path_lower.endswith(".parquet"):
        df = spark.read.parquet(station_master_path)
    else:
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(station_master_path)
        )

    columns_lower = {col.lower(): col for col in df.columns}

    station_col = (
        columns_lower.get("station")
        or columns_lower.get("station_id")
        or columns_lower.get("usaf_wban")
    )

    state_col = columns_lower.get("state")

    begin_col = (
        columns_lower.get("begin")
        or columns_lower.get("begin_date")
    )

    end_col = (
        columns_lower.get("end")
        or columns_lower.get("end_date")
    )

    if station_col is None:
        raise ValueError(
            "Station master must contain one of these columns: "
            "station, station_id, or usaf_wban."
        )

    if state_col is None:
        raise ValueError("Station master must contain a state column.")

    selected_states = [state.upper() for state in states]

    station_df = (
        df.withColumnRenamed(station_col, "station_id")
        .withColumnRenamed(state_col, "state")
        .withColumn("station_id", F.col("station_id").cast("string"))
        .withColumn("state", F.upper(F.col("state")))
        .filter(F.col("state").isin(selected_states))
    )

    if begin_col is not None:
        station_df = station_df.withColumn(
            "begin_year",
            F.substring(F.col(begin_col).cast("string"), 1, 4).cast("int"),
        )
    else:
        station_df = station_df.withColumn("begin_year", F.lit(None).cast("int"))

    if end_col is not None:
        station_df = station_df.withColumn(
            "end_year",
            F.substring(F.col(end_col).cast("string"), 1, 4).cast("int"),
        )
    else:
        station_df = station_df.withColumn("end_year", F.lit(None).cast("int"))

    station_df = (
        station_df
        .select("station_id", "state", "begin_year", "end_year")
        .dropDuplicates(["station_id"])
        .orderBy("station_id")
    )

    if max_stations is not None:
        station_df = station_df.limit(max_stations)

    return station_df


def build_noaa_paths_from_station_rows(
    raw_isd_root: str,
    station_rows: list[Row],
    years: list[int],
) -> list[str]:
    """
    NOAA layout:
    s3a://noaa-global-hourly-pds/<year>/<station>.csv

    Uses station begin/end years to avoid generating impossible station-year paths.
    """
    paths: list[str] = []
    raw_isd_root = raw_isd_root.rstrip("/")

    skipped_by_date_range = 0

    for row in station_rows:
        station_id = row["station_id"]
        begin_year = row["begin_year"]
        end_year = row["end_year"]

        for year in years:
            if begin_year is not None and year < begin_year:
                skipped_by_date_range += 1
                continue

            if end_year is not None and year > end_year:
                skipped_by_date_range += 1
                continue

            paths.append(f"{raw_isd_root}/{year}/{station_id}.csv")

    logger.info(
        "NOAA candidate paths generated: %s; skipped_by_station_active_range=%s",
        len(paths),
        skipped_by_date_range,
    )

    return paths


def filter_existing_paths(spark: SparkSession, paths: list[str]) -> list[str]:
    """
    Keep only S3 paths that actually exist before Spark tries to read them.
    """
    jvm = spark.sparkContext._jvm
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()

    existing_paths: list[str] = []
    missing_count = 0

    for path in paths:
        j_path = jvm.org.apache.hadoop.fs.Path(path)
        fs = j_path.getFileSystem(hadoop_conf)

        if fs.exists(j_path):
            existing_paths.append(path)
        else:
            missing_count += 1
            logger.debug("Skipping missing file: %s", path)

    logger.info(
        "Path existence check complete: existing=%s missing=%s total=%s",
        len(existing_paths),
        missing_count,
        len(paths),
    )

    return existing_paths


def read_raw_isd_csv(spark: SparkSession, paths: list[str]) -> DataFrame:
    """
    Read only NOAA ISD CSV files that exist.
    """
    if not paths:
        raise ValueError("No NOAA paths were generated.")

    existing_paths = filter_existing_paths(spark, paths)

    if not existing_paths:
        raise ValueError(
            "None of the generated NOAA paths exist. "
            "Check station IDs, years, station active ranges, and NOAA path format."
        )

    logger.info("Existing input files: %s / %s", len(existing_paths), len(paths))

    return (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .option("mode", "PERMISSIVE")
        .csv(existing_paths)
    )


def add_bronze_metadata(df: DataFrame) -> DataFrame:
    ingested_at = datetime.now(timezone.utc).isoformat()

    return (
        df.withColumn("ingested_at_utc", F.lit(ingested_at))
        .withColumn("ingest_source", F.lit("noaa-global-hourly-pds"))
        .withColumn("ingest_layer", F.lit("bronze"))
        .withColumn("year", F.year(F.to_timestamp(F.col("DATE"))))
    )


def main() -> None:
    args = parse_args()

    spark = get_spark_session(app_name="layer5_ingest_raw_isd_to_bronze")
    paths = Paths()

    station_master_df = load_station_master(
        spark=spark,
        station_master_path=args.station_master_path,
        states=args.states,
        max_stations=args.max_stations,
    )

    station_rows = station_master_df.collect()

    if not station_rows:
        raise ValueError(
            f"No stations found for states={args.states}. "
            "Check station master file and state column."
        )

    noaa_paths = build_noaa_paths_from_station_rows(
        raw_isd_root=paths.raw_isd,
        station_rows=station_rows,
        years=args.years,
    )

    logger.info("Starting bronze ingestion")
    logger.info("Active project bucket: %s", config.aws["project_bucket"])
    logger.info("Raw NOAA root: %s", paths.raw_isd)
    logger.info("Bronze output: %s", paths.bronze_isd)
    logger.info("Years: %s", args.years)
    logger.info("States: %s", args.states)
    logger.info("Stations: %s", len(station_rows))
    logger.info("Candidate input files after active-range filtering: %s", len(noaa_paths))
    logger.info("Write mode: %s", args.mode)

    raw_df = read_raw_isd_csv(spark=spark, paths=noaa_paths)
    bronze_df = add_bronze_metadata(raw_df)

    compacted_df = compact_for_bronze(
        df=bronze_df,
        partition_col="year",
        target_files_per_partition=args.target_files_per_year,
    )

    write_bronze(
        df=compacted_df,
        output_path=paths.bronze_isd,
        partition_cols=["year"],
        mode=args.mode,
    )

    logger.info("Bronze ingestion complete.")
    logger.info("Output written to: %s", paths.bronze_isd)

    spark.stop()


if __name__ == "__main__":
    main()