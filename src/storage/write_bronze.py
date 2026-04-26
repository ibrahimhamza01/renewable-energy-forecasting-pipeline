# src/storage/write_bronze.py

from __future__ import annotations

from pyspark.sql import DataFrame


def write_bronze(
    df: DataFrame,
    output_path: str,
    partition_cols: list[str],
    mode: str = "overwrite",
) -> None:
    """
    Write raw-but-organized bronze data as partitioned Parquet.
    """
    (
        df.write
        .mode(mode)
        .partitionBy(*partition_cols)
        .parquet(output_path)
    )