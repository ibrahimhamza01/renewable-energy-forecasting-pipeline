"""
Parser for NOAA ISD DEW field.

Observed raw format:
    DEW = "dew_point,dew_point_qc"

Example:
    "+0078,1"

Interpretation:
    - dew_point: dew point temperature in tenths of degrees Celsius
    - dew_point_qc: quality control flag

Examples:
    "+0078" -> 7.8 C
    "-0123" -> -12.3 C

Sentinel patterns observed:
    - +9999 -> missing
    - -9999 -> missing

This module provides Spark DataFrame transformations for parsing DEW.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


DEW_PART_COUNT = 2
DEW_SENTINELS = {"+9999", "-9999"}


def add_parsed_dew_columns(df: DataFrame, source_col: str = "DEW") -> DataFrame:
    """
    Add parsed NOAA ISD DEW columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded DEW column.
    source_col : str
        Name of the source column to parse. Defaults to "DEW".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed DEW columns appended.

    Output columns
    --------------
    - dew_point_c  : double degrees Celsius, null if missing/malformed
    - dew_point_qc : string QC flag
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    dew_point_raw_col = f"{source_col}_dew_point_raw_tmp"
    dew_point_qc_col = f"{source_col}_dew_point_qc_tmp"

    result = (
        df.withColumn(
            dew_point_raw_col,
            F.when(F.size(parts) == DEW_PART_COUNT, F.trim(parts.getItem(0))),
        )
        .withColumn(
            dew_point_qc_col,
            F.when(F.size(parts) == DEW_PART_COUNT, F.trim(parts.getItem(1))),
        )
        .withColumn(
            "dew_point_c",
            F.when(
                F.col(dew_point_raw_col).isNull()
                | (F.col(dew_point_raw_col) == "")
                | F.col(dew_point_raw_col).isin(*DEW_SENTINELS),
                F.lit(None),
            ).otherwise(F.expr(f"try_cast({dew_point_raw_col} as int) / 10.0"))
        )
        .withColumn("dew_point_qc", F.col(dew_point_qc_col))
        .drop(dew_point_raw_col, dew_point_qc_col)
    )

    return result