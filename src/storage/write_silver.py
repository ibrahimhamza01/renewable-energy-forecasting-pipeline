from __future__ import annotations

import argparse

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.paths import Paths
from src.common.spark_utils import get_spark_session
from src.parsing.parse_all_fields import add_all_parsed_weather_columns
from src.cleaning.clean_isd import build_cleaned_weather_table
from src.cleaning.enrich_with_station_metadata import enrich_with_station_metadata


def write_silver(
    df: DataFrame,
    output_path: str,
    partition_cols: list[str],
    mode: str = "overwrite",
) -> None:
    (
        df.write
        .mode(mode)
        .partitionBy(*partition_cols)
        .parquet(output_path)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build silver weather table from bronze ISD data."
    )

    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        required=True,
        help="Years to process, e.g. --years 2018 2019 2020",
    )

    parser.add_argument(
        "--station-master-path",
        required=True,
        help="Path to station master CSV or Parquet.",
    )

    return parser.parse_args()


def normalize_bronze_columns(df: DataFrame) -> DataFrame:
    out = df

    if "STATION" in out.columns and "station_id" not in out.columns:
        out = out.withColumn("station_id", F.col("STATION").cast("string"))

    if "DATE" in out.columns and "timestamp_utc" not in out.columns:
        out = out.withColumn("timestamp_utc", F.to_timestamp(F.col("DATE")))

    return out


def load_station_master(spark: SparkSession, path: str) -> DataFrame:
    if path.lower().endswith(".parquet"):
        df = spark.read.parquet(path)
    else:
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(path)
        )

    rename_map = {
        "station": "station_id",
        "STATION": "station_id",
        "station name": "station_name",
        "STATION NAME": "station_name",
        "ctry": "country_code",
        "CTRY": "country_code",
        "lat": "latitude",
        "LAT": "latitude",
        "lon": "longitude",
        "LON": "longitude",
        "elev(m)": "elevation_m",
        "ELEV(M)": "elevation_m",
        "begin": "begin_date",
        "BEGIN": "begin_date",
        "end": "end_date",
        "END": "end_date",
    }

    for old, new in rename_map.items():
        if old in df.columns and new not in df.columns:
            df = df.withColumnRenamed(old, new)

    if "station_id" not in df.columns:
        raise ValueError("Station master must contain station or station_id.")

    df = df.withColumn("station_id", F.col("station_id").cast("string"))

    if "state" in df.columns:
        df = df.withColumn("state", F.upper(F.col("state")))

    if "begin_date" in df.columns:
        df = df.withColumn(
            "begin_year",
            F.substring(F.col("begin_date").cast("string"), 1, 4).cast("int"),
        )

    if "end_date" in df.columns:
        df = df.withColumn(
            "end_year",
            F.substring(F.col("end_date").cast("string"), 1, 4).cast("int"),
        )

    return df


def main() -> None:
    args = parse_args()

    spark = get_spark_session(app_name="layer5_part_b_build_silver_weather")
    paths = Paths()

    print(f"Reading bronze from: {paths.bronze_isd}")
    bronze_df = spark.read.parquet(paths.bronze_isd)
    bronze_df = bronze_df.filter(F.col("year").isin(args.years))

    normalized_df = normalize_bronze_columns(bronze_df)

    parsed_df = add_all_parsed_weather_columns(normalized_df)

    cleaned_df = build_cleaned_weather_table(
        parsed_df,
        keep_extra_columns=True,
    )

    station_df = load_station_master(
        spark=spark,
        path=args.station_master_path,
    )

    silver_df = enrich_with_station_metadata(
        weather_df=cleaned_df,
        station_df=station_df,
        station_col="station_id",
    )

    print(f"Writing silver to: {paths.silver_weather}")

    write_silver(
        df=silver_df,
        output_path=paths.silver_weather,
        partition_cols=["year", "state"],
        mode="overwrite",
    )

    print("Silver weather table complete.")

    spark.stop()


if __name__ == "__main__":
    main()