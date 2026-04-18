"""
Parser for NOAA ISD WND field.

Observed raw format:
    WND = "direction,direction_qc,type_code,speed,speed_qc"

Example:
    "324,1,H,0051,1"

Interpretation:
    - direction: wind direction in angular degrees
    - direction_qc: quality control flag for direction
    - type_code: observation type code
    - speed: wind speed in tenths of meters per second
    - speed_qc: quality control flag for speed

Sentinel patterns observed:
    - direction = 999  -> missing
    - speed = 9999     -> missing

This module provides Spark DataFrame transformations for parsing WND.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


WND_PART_COUNT = 5
DIRECTION_SENTINEL = "999"
SPEED_SENTINEL = "9999"


def add_parsed_wnd_columns(df: DataFrame, source_col: str = "WND") -> DataFrame:
    """
    Add parsed NOAA ISD WND columns to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the encoded WND column.
    source_col : str
        Name of the source column to parse. Defaults to "WND".

    Returns
    -------
    DataFrame
        Spark DataFrame with parsed WND columns appended.
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found in dataframe.")

    parts = F.split(F.col(source_col), ",")

    direction_raw = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(0)))
    direction_qc = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(1)))
    type_code = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(2)))
    speed_raw = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(3)))
    speed_qc = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(4)))

    direction_int = direction_raw.cast("int")
    speed_int = speed_raw.cast("int")

    wind_direction_degrees = (
        F.when(
            direction_raw.isNull()
            | (direction_raw == "")
            | (direction_raw == DIRECTION_SENTINEL),
            F.lit(None),
        )
        .when(direction_int.isNull(), F.lit(None))
        .when((direction_int < 0) | (direction_int > 360), F.lit(None))
        .otherwise(direction_int)
    )

    wind_speed_ms = (
        F.when(
            speed_raw.isNull()
            | (speed_raw == "")
            | (speed_raw == SPEED_SENTINEL),
            F.lit(None),
        )
        .when(speed_int.isNull(), F.lit(None))
        .when(speed_int < 0, F.lit(None))
        .otherwise(speed_int / F.lit(10.0))
    )

    return (
        df.withColumn("wind_direction_degrees", wind_direction_degrees)
        .withColumn("wind_direction_qc", direction_qc)
        .withColumn("wind_observation_type", type_code)
        .withColumn("wind_speed_ms", wind_speed_ms)
        .withColumn("wind_speed_qc", speed_qc)
    )