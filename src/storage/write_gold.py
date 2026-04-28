"""
Layer 6 Part B: Gold table writing utilities.

All paths must be resolved before calling these functions.
This module does not hardcode S3 buckets or prefixes.
"""

from __future__ import annotations

from pyspark.sql import DataFrame


def write_gold_table(
    df: DataFrame,
    output_path: str,
    partition_cols: list[str] | None = None,
    mode: str = "overwrite",
) -> None:
    if partition_cols:
        df = df.repartition(64, *partition_cols)

    writer = (
        df.write
        .mode(mode)
        .format("parquet")
        .option("compression", "snappy")
        .option("partitionOverwriteMode", "dynamic")
    )

    if partition_cols:
        writer = writer.partitionBy(*partition_cols)

    writer.save(output_path)


def write_hourly_station_wind_gold(df: DataFrame, output_path: str) -> None:
    write_gold_table(df, output_path, ["year", "state"], mode="overwrite")


def write_daily_station_wind_gold(df: DataFrame, output_path: str) -> None:
    write_gold_table(df, output_path, ["year", "state"], mode="overwrite")


def write_daily_region_wind_gold(df: DataFrame, output_path: str) -> None:
    write_gold_table(df, output_path, ["year", "state"], mode="overwrite")


def write_monthly_region_wind_gold(df: DataFrame, output_path: str) -> None:
    write_gold_table(df, output_path, ["year", "state"], mode="overwrite")