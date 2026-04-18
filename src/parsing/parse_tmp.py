"""
Parser for NOAA ISD TMP field.

Observed raw format:
    TMP = "temperature,temperature_qc"

Example:
    "+0093,1"

Interpretation:
    - temperature: air temperature in tenths of degrees Celsius
    - temperature_qc: quality control flag

Examples:
    "+0093" -> 9.3 C
    "-0050" -> -5.0 C

Sentinel patterns observed:
    - +9999 -> missing
    - -9999 -> missing

This module provides Spark DataFrame transformations for parsing TMP.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


TMP_PART_COUNT = 2
TMP_SENTINELS = {"+9999", "-9999"}


def add_parsed_tmp_columns(df: DataFrame, source_col: str = "TMP") -> DataFrame:
    """
    Add parsed NOAA ISD TMP columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded TMP column.
    source_col : str
        Name of the source column to parse. Defaults to "TMP".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed TMP columns appended.
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    temperature_raw_col = f"{source_col}_temperature_raw_tmp"
    temperature_qc_col = f"{source_col}_temperature_qc_tmp"

    result = (
        df.withColumn(
            temperature_raw_col,
            F.when(F.size(parts) == TMP_PART_COUNT, F.trim(parts.getItem(0))),
        )
        .withColumn(
            temperature_qc_col,
            F.when(F.size(parts) == TMP_PART_COUNT, F.trim(parts.getItem(1))),
        )
        .withColumn(
            "temperature_c",
            F.when(
                F.col(temperature_raw_col).isNull()
                | (F.col(temperature_raw_col) == "")
                | F.col(temperature_raw_col).isin(*TMP_SENTINELS),
                F.lit(None),
            ).otherwise(F.expr(f"try_cast({temperature_raw_col} as int) / 10.0"))
        )
        .withColumn("temperature_qc", F.col(temperature_qc_col))
        .drop(temperature_raw_col, temperature_qc_col)
    )

    return result