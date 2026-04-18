"""
Parser for NOAA ISD VIS field.

Observed raw format:
    VIS = "visibility_distance,visibility_distance_qc,visibility_variability,visibility_variability_qc"

Example:
    "016093,1,N,1"

Interpretation:
    - visibility_distance: horizontal visibility distance in meters
    - visibility_distance_qc: quality control flag
    - visibility_variability: variability flag/code
    - visibility_variability_qc: quality control flag for variability

Examples:
    "016093" -> 16093 meters

Sentinel patterns observed:
    - 999999 -> missing visibility distance

This module provides Spark DataFrame transformations for parsing VIS.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


VIS_PART_COUNT = 4
VIS_DISTANCE_SENTINELS = {"999999"}


def add_parsed_vis_columns(df: DataFrame, source_col: str = "VIS") -> DataFrame:
    """
    Add parsed NOAA ISD VIS columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded VIS column.
    source_col : str
        Name of the source column to parse. Defaults to "VIS".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed VIS columns appended.

    Output columns
    --------------
    - visibility_distance_m      : double meters, null if missing/malformed
    - visibility_distance_qc     : string QC flag
    - visibility_variability     : string variability flag/code
    - visibility_variability_qc  : string QC flag
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    distance_raw_col = f"{source_col}_visibility_distance_raw_tmp"
    distance_qc_col = f"{source_col}_visibility_distance_qc_tmp"
    variability_col = f"{source_col}_visibility_variability_tmp"
    variability_qc_col = f"{source_col}_visibility_variability_qc_tmp"

    result = (
        df.withColumn(
            distance_raw_col,
            F.when(F.size(parts) == VIS_PART_COUNT, F.trim(parts.getItem(0))),
        )
        .withColumn(
            distance_qc_col,
            F.when(F.size(parts) == VIS_PART_COUNT, F.trim(parts.getItem(1))),
        )
        .withColumn(
            variability_col,
            F.when(F.size(parts) == VIS_PART_COUNT, F.trim(parts.getItem(2))),
        )
        .withColumn(
            variability_qc_col,
            F.when(F.size(parts) == VIS_PART_COUNT, F.trim(parts.getItem(3))),
        )
        .withColumn(
            "visibility_distance_m",
            F.when(
                F.col(distance_raw_col).isNull()
                | (F.col(distance_raw_col) == "")
                | F.col(distance_raw_col).isin(*VIS_DISTANCE_SENTINELS),
                F.lit(None),
            ).otherwise(F.expr(f"try_cast({distance_raw_col} as int) * 1.0"))
        )
        .withColumn("visibility_distance_qc", F.col(distance_qc_col))
        .withColumn("visibility_variability", F.col(variability_col))
        .withColumn("visibility_variability_qc", F.col(variability_qc_col))
        .drop(
            distance_raw_col,
            distance_qc_col,
            variability_col,
            variability_qc_col,
        )
    )

    return result