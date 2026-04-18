"""
Parser for NOAA ISD SLP field.

Observed raw format:
    SLP = "sea_level_pressure,sea_level_pressure_qc"

Example:
    "10132,1"

Interpretation:
    - sea_level_pressure: sea level pressure in tenths of hPa
    - sea_level_pressure_qc: quality control flag

Examples:
    "10132" -> 1013.2 hPa

Sentinel patterns observed:
    - 99999 -> missing

This module provides Spark DataFrame transformations for parsing SLP.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


SLP_PART_COUNT = 2
SLP_SENTINELS = {"99999"}


def add_parsed_slp_columns(df: DataFrame, source_col: str = "SLP") -> DataFrame:
    """
    Add parsed NOAA ISD SLP columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded SLP column.
    source_col : str
        Name of the source column to parse. Defaults to "SLP".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed SLP columns appended.

    Output columns
    --------------
    - sea_level_pressure_hpa : double hPa, null if missing/malformed
    - sea_level_pressure_qc  : string QC flag
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    slp_raw_col = f"{source_col}_sea_level_pressure_raw_tmp"
    slp_qc_col = f"{source_col}_sea_level_pressure_qc_tmp"

    result = (
        df.withColumn(
            slp_raw_col,
            F.when(F.size(parts) == SLP_PART_COUNT, F.trim(parts.getItem(0))),
        )
        .withColumn(
            slp_qc_col,
            F.when(F.size(parts) == SLP_PART_COUNT, F.trim(parts.getItem(1))),
        )
        .withColumn(
            "sea_level_pressure_hpa",
            F.when(
                F.col(slp_raw_col).isNull()
                | (F.col(slp_raw_col) == "")
                | F.col(slp_raw_col).isin(*SLP_SENTINELS),
                F.lit(None),
            ).otherwise(F.expr(f"try_cast({slp_raw_col} as int) / 10.0"))
        )
        .withColumn("sea_level_pressure_qc", F.col(slp_qc_col))
        .drop(slp_raw_col, slp_qc_col)
    )

    return result