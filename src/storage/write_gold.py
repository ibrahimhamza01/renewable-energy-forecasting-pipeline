"""
Layer 6 Part B: Write gold wind tables to S3.

Reads validated silver weather data, applies wind power curve,
generates gold tables at multiple aggregation grains, and writes
them as partitioned Parquet to S3.
"""

from __future__ import annotations

from pyspark.sql import DataFrame


def write_gold(
    df: DataFrame,
    output_path: str,
    partition_cols: list[str],
    mode: str = "overwrite",
) -> None:
    """Write a gold DataFrame to S3 as partitioned Parquet."""
    (
        df.write
        .mode(mode)
        .partitionBy(*partition_cols)
        .parquet(output_path)
    )
    print(f"Gold table written to: {output_path}")
