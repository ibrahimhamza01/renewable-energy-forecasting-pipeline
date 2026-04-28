"""
Layer 6 Part B: Build Gold wind tables from Silver weather data.
"""

from __future__ import annotations

import argparse
import os

import yaml
from pyspark.sql import functions as F

from src.common.spark_utils import get_spark_session
from src.storage.table_builders import (
    build_wind_gold_tables_from_silver_df,
    write_wind_gold_tables,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["sample", "full"],
        default="sample",
        help="Run sample validation or full Gold build.",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Optional year filter, for example --year 2025.",
    )

    return parser.parse_args()


def load_user_config() -> dict:
    config_path = os.environ.get("PROJECT_USER_CONFIG")

    if not config_path:
        raise RuntimeError("PROJECT_USER_CONFIG is not set")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def s3_path(bucket: str, prefix: str) -> str:
    return f"s3a://{bucket}/{prefix.strip('/')}"


def main() -> None:
    args = parse_args()
    user_config = load_user_config()

    bucket = user_config["aws"]["project_bucket"]
    silver_prefix = user_config["aws"]["silver_prefix"]
    gold_prefix = user_config["aws"]["gold_prefix"]

    silver_path = s3_path(bucket, silver_prefix)

    gold_root = "gold/wind_sample_test" if args.mode == "sample" else gold_prefix

    gold_hourly_station_path = s3_path(bucket, f"{gold_root}/station/hourly")
    gold_daily_station_path = s3_path(bucket, f"{gold_root}/station/daily")
    gold_daily_region_path = s3_path(bucket, f"{gold_root}/region/daily")
    gold_monthly_region_path = s3_path(bucket, f"{gold_root}/region/monthly")

    spark = get_spark_session(
        app_name=f"layer6_partB_gold_wind_{args.mode}"
    )

    print("=== Layer 6 Part B: Gold Wind Table Build ===")
    print(f"Mode: {args.mode}")
    print(f"Year filter: {args.year if args.year is not None else 'ALL'}")
    print(f"Reading Silver from: {silver_path}")
    print(f"Writing hourly station Gold to: {gold_hourly_station_path}")
    print(f"Writing daily station Gold to: {gold_daily_station_path}")
    print(f"Writing daily region Gold to: {gold_daily_region_path}")
    print(f"Writing monthly region Gold to: {gold_monthly_region_path}")

    silver_df = spark.read.parquet(silver_path)

    if args.mode == "sample":
        print("Applying SAMPLE filter: state=TX")
        silver_df = silver_df.where(F.col("state") == "TX")

        if args.year is None:
            print("No sample year provided; defaulting sample year to 2010")
            silver_df = silver_df.where(F.col("year") == 2010)

    if args.year is not None:
        print(f"Applying year filter: year={args.year}")
        silver_df = silver_df.where(F.col("year") == args.year)

    silver_df = silver_df.where(
        F.col("wind_speed_ms").isNotNull()
        & (F.col("wind_speed_ms") >= 0)
        & (F.col("wind_speed_ms") < 120)
    )

    if args.mode == "sample":
        total_rows = silver_df.count()
        print(f"Input rows after filters: {total_rows:,}")

        if total_rows == 0:
            raise RuntimeError("No rows found after filters. Aborting Gold build.")
    else:
        print("Skipping input row count in full mode.")

    tables = build_wind_gold_tables_from_silver_df(silver_df)

    if args.mode == "sample":
        print("Counts before write:")
        for table_name, df in tables.items():
            print(f"{table_name}: {df.count():,}")
    else:
        print("Skipping pre-write table counts in full mode.")

    print("Writing Gold tables...")
    write_wind_gold_tables(
        tables=tables,
        gold_hourly_station_path=gold_hourly_station_path,
        gold_daily_station_path=gold_daily_station_path,
        gold_daily_region_path=gold_daily_region_path,
        gold_monthly_region_path=gold_monthly_region_path,
    )

    output_paths = {
        "hourly_station": gold_hourly_station_path,
        "daily_station": gold_daily_station_path,
        "daily_region": gold_daily_region_path,
        "monthly_region": gold_monthly_region_path,
    }

    if args.mode == "sample":
        print("Validating written Gold outputs:")
        for table_name, path in output_paths.items():
            df = spark.read.parquet(path)
            print(f"{table_name}: {df.count():,}")
            df.show(5, truncate=False)
    else:
        print("Skipping full read-back validation in full mode.")
        print("Run targeted validation separately after the full job completes.")

    print("=== Layer 6 Part B Gold build complete ===")

    spark.stop()


if __name__ == "__main__":
    main()