# src/common/io_utils.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pyspark.sql import DataFrame, SparkSession


def ensure_directory(path: str) -> None:
    """
    Ensure a local directory exists.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def write_parquet(
    df: DataFrame,
    output_path: str,
    mode: str = "overwrite",
    partition_cols: Sequence[str] | None = None,
) -> None:
    """
    Write a Spark DataFrame to Parquet.
    """
    ensure_directory(str(Path(output_path).parent))

    writer = df.write.mode(mode)

    if partition_cols:
        writer = writer.partitionBy(*partition_cols)

    writer.parquet(output_path)


def read_parquet(
    spark: SparkSession,
    input_path: str,
) -> DataFrame:
    """
    Read a Parquet dataset from a local path.
    """
    return spark.read.parquet(input_path)