"""
Parser for NOAA ISD CIG field.

Observed raw format:
    CIG = "ceiling_height,ceiling_height_qc,ceiling_determination_code,ceiling_cavok"

Example:
    "02200,1,5,0"

Interpretation:
    - ceiling_height: ceiling height in meters
    - ceiling_height_qc: quality control flag
    - ceiling_determination_code: method/code used for ceiling determination
    - ceiling_cavok: CAVOK indicator/code

Examples:
    "02200" -> 2200 meters

Sentinel patterns observed:
    - 99999 -> missing ceiling height

This module provides Spark DataFrame transformations for parsing CIG.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


CIG_PART_COUNT = 4
CIG_HEIGHT_SENTINELS = {"99999"}


def add_parsed_cig_columns(df: DataFrame, source_col: str = "CIG") -> DataFrame:
    """
    Add parsed NOAA ISD CIG columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded CIG column.
    source_col : str
        Name of the source column to parse. Defaults to "CIG".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed CIG columns appended.

    Output columns
    --------------
    - ceiling_height_m            : double meters, null if missing/malformed
    - ceiling_height_qc           : string QC flag
    - ceiling_determination_code  : string determination code
    - ceiling_cavok               : string CAVOK indicator/code
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    height_raw_col = f"{source_col}_ceiling_height_raw_tmp"
    height_qc_col = f"{source_col}_ceiling_height_qc_tmp"
    determination_col = f"{source_col}_ceiling_determination_tmp"
    cavok_col = f"{source_col}_ceiling_cavok_tmp"

    result = (
        df.withColumn(
            height_raw_col,
            F.when(F.size(parts) == CIG_PART_COUNT, F.trim(parts.getItem(0))),
        )
        .withColumn(
            height_qc_col,
            F.when(F.size(parts) == CIG_PART_COUNT, F.trim(parts.getItem(1))),
        )
        .withColumn(
            determination_col,
            F.when(F.size(parts) == CIG_PART_COUNT, F.trim(parts.getItem(2))),
        )
        .withColumn(
            cavok_col,
            F.when(F.size(parts) == CIG_PART_COUNT, F.trim(parts.getItem(3))),
        )
        .withColumn(
            "ceiling_height_m",
            F.when(
                F.col(height_raw_col).isNull()
                | (F.col(height_raw_col) == "")
                | F.col(height_raw_col).isin(*CIG_HEIGHT_SENTINELS),
                F.lit(None),
            ).otherwise(F.expr(f"try_cast({height_raw_col} as int) * 1.0"))
        )
        .withColumn("ceiling_height_qc", F.col(height_qc_col))
        .withColumn("ceiling_determination_code", F.col(determination_col))
        .withColumn("ceiling_cavok", F.col(cavok_col))
        .drop(
            height_raw_col,
            height_qc_col,
            determination_col,
            cavok_col,
        )
    )

    return result