# src/cleaning/standardize_units.py

# NOTE:
# Unit standardization is currently performed in Layer 2 parsing.
# This module is retained for future extensibility or alternate pipelines.

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

KNOT_TO_MPS = 0.514444
TENTHS_SCALE = 10.0

# NOAA/ISD parsed values are often stored in tenths for temperature/dew/pressure.
# This module assumes your Layer 2 parsers produced the common raw parsed columns
# below. If your parser names differ, adjust the function arguments in clean_isd.py.
#
# Intended outcomes:
# - wind_speed_ms
# - temperature_c
# - dew_point_c
# - sea_level_pressure_hpa
# - timestamp_utc
#
# This file focuses on unit normalization and timestamp normalization only.
# QC filtering / sentinel handling should stay in quality_filters.py.


# ------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------

def _round_if_not_null(col_name: str, digits: int) -> F.Column:
    return F.when(F.col(col_name).isNull(), F.lit(None)).otherwise(
        F.round(F.col(col_name), digits)
    )


def _normalize_timestamp_string(date_col: str) -> F.Column:
    """
    Normalize common timestamp strings into a Spark timestamp.

    NOAA DATE values are typically ISO-like, for example:
    - 2020-01-15T23:00:00
    - 2020-01-15T23:00:00Z

    This helper strips a trailing 'Z' if present, then parses as UTC-naive
    timestamp text. The result column itself should be treated as UTC.
    """
    cleaned = F.regexp_replace(F.trim(F.col(date_col).cast("string")), r"Z$", "")
    return F.to_timestamp(cleaned, "yyyy-MM-dd'T'HH:mm:ss")


# ------------------------------------------------------------------------------
# Wind speed
# ------------------------------------------------------------------------------

def standardize_wind_speed(
    df: DataFrame,
    source_col: str = "wind_speed",
    target_col: str = "wind_speed_ms",
    source_unit: str = "knots",
    round_digits: int = 3,
) -> DataFrame:
    """
    Convert wind speed to meters per second.

    Supported source_unit values:
    - "knots"
    - "m/s"
    - "ms"
    """
    if source_col not in df.columns:
        return df

    unit = source_unit.strip().lower()
    if unit not in {"knots", "m/s", "ms"}:
        raise ValueError(
            f"Unsupported wind speed unit '{source_unit}'. "
            "Supported values are: 'knots', 'm/s', 'ms'."
        )

    if unit == "knots":
        expr = F.col(source_col) * F.lit(KNOT_TO_MPS)
    else:
        expr = F.col(source_col)

    out = df.withColumn(target_col, expr)
    out = out.withColumn(target_col, _round_if_not_null(target_col, round_digits))
    return out


# ------------------------------------------------------------------------------
# Temperature / dew point
# ------------------------------------------------------------------------------

def standardize_temperature_like_column(
    df: DataFrame,
    source_col: str,
    target_col: str,
    source_unit: str = "tenths_c",
    round_digits: int = 1,
) -> DataFrame:
    """
    Standardize temperature-like columns to degrees Celsius.

    Supported source_unit values:
    - "tenths_c" : NOAA style integer tenths of degrees C
    - "c"        : already Celsius
    - "f"        : Fahrenheit
    """
    if source_col not in df.columns:
        return df

    unit = source_unit.strip().lower()
    if unit == "tenths_c":
        expr = F.col(source_col) / F.lit(TENTHS_SCALE)
    elif unit == "c":
        expr = F.col(source_col)
    elif unit == "f":
        expr = (F.col(source_col) - F.lit(32.0)) * F.lit(5.0 / 9.0)
    else:
        raise ValueError(
            f"Unsupported temperature unit '{source_unit}'. "
            "Supported values are: 'tenths_c', 'c', 'f'."
        )

    out = df.withColumn(target_col, expr)
    out = out.withColumn(target_col, _round_if_not_null(target_col, round_digits))
    return out


def standardize_temperature(
    df: DataFrame,
    source_col: str = "temperature",
    target_col: str = "temperature_c",
    source_unit: str = "tenths_c",
    round_digits: int = 1,
) -> DataFrame:
    return standardize_temperature_like_column(
        df=df,
        source_col=source_col,
        target_col=target_col,
        source_unit=source_unit,
        round_digits=round_digits,
    )


def standardize_dew_point(
    df: DataFrame,
    source_col: str = "dew_point",
    target_col: str = "dew_point_c",
    source_unit: str = "tenths_c",
    round_digits: int = 1,
) -> DataFrame:
    return standardize_temperature_like_column(
        df=df,
        source_col=source_col,
        target_col=target_col,
        source_unit=source_unit,
        round_digits=round_digits,
    )


# ------------------------------------------------------------------------------
# Pressure / visibility / ceiling
# ------------------------------------------------------------------------------

def standardize_sea_level_pressure(
    df: DataFrame,
    source_col: str = "sea_level_pressure",
    target_col: str = "sea_level_pressure_hpa",
    source_unit: str = "tenths_hpa",
    round_digits: int = 1,
) -> DataFrame:
    """
    Standardize sea level pressure to hPa.

    Supported source_unit values:
    - "tenths_hpa"
    - "hpa"
    - "pa"
    """
    if source_col not in df.columns:
        return df

    unit = source_unit.strip().lower()
    if unit == "tenths_hpa":
        expr = F.col(source_col) / F.lit(TENTHS_SCALE)
    elif unit == "hpa":
        expr = F.col(source_col)
    elif unit == "pa":
        expr = F.col(source_col) / F.lit(100.0)
    else:
        raise ValueError(
            f"Unsupported pressure unit '{source_unit}'. "
            "Supported values are: 'tenths_hpa', 'hpa', 'pa'."
        )

    out = df.withColumn(target_col, expr)
    out = out.withColumn(target_col, _round_if_not_null(target_col, round_digits))
    return out


def standardize_visibility(
    df: DataFrame,
    source_col: str = "visibility",
    target_col: str = "visibility_m",
    source_unit: str = "m",
    round_digits: int = 1,
) -> DataFrame:
    """
    Standardize visibility to meters.

    Supported source_unit values:
    - "m"
    - "km"
    """
    if source_col not in df.columns:
        return df

    unit = source_unit.strip().lower()
    if unit == "m":
        expr = F.col(source_col)
    elif unit == "km":
        expr = F.col(source_col) * F.lit(1000.0)
    else:
        raise ValueError(
            f"Unsupported visibility unit '{source_unit}'. "
            "Supported values are: 'm', 'km'."
        )

    out = df.withColumn(target_col, expr)
    out = out.withColumn(target_col, _round_if_not_null(target_col, round_digits))
    return out


def standardize_ceiling_height(
    df: DataFrame,
    source_col: str = "ceiling_height",
    target_col: str = "ceiling_height_m",
    source_unit: str = "m",
    round_digits: int = 1,
) -> DataFrame:
    """
    Standardize ceiling height to meters.

    Supported source_unit values:
    - "m"
    - "ft"
    """
    if source_col not in df.columns:
        return df

    unit = source_unit.strip().lower()
    if unit == "m":
        expr = F.col(source_col)
    elif unit == "ft":
        expr = F.col(source_col) * F.lit(0.3048)
    else:
        raise ValueError(
            f"Unsupported ceiling height unit '{source_unit}'. "
            "Supported values are: 'm', 'ft'."
        )

    out = df.withColumn(target_col, expr)
    out = out.withColumn(target_col, _round_if_not_null(target_col, round_digits))
    return out


# ------------------------------------------------------------------------------
# Timestamp normalization
# ------------------------------------------------------------------------------

def normalize_timestamp(
    df: DataFrame,
    source_col: str = "timestamp",
    target_col: str = "timestamp_utc",
    year_col: str = "year",
    month_col: str = "month",
    day_col: str = "day",
    hour_col: str = "hour",
) -> DataFrame:
    """
    Normalize timestamp to a Spark timestamp column in UTC.

    Supported patterns:
    1. source_col exists and contains an ISO-like datetime string
    2. source_col does not exist, but year/month/day/hour columns exist

    Added outputs:
    - target_col
    - date_utc
    - year
    - month
    - day
    - hour

    Existing partition columns are overwritten from the normalized timestamp so
    downstream partitioning stays consistent.
    """
    out = df

    if source_col in out.columns:
        out = out.withColumn(target_col, _normalize_timestamp_string(source_col))
    elif {year_col, month_col, day_col, hour_col}.issubset(set(out.columns)):
        out = out.withColumn(
            target_col,
            F.to_timestamp(
                F.format_string(
                    "%04d-%02d-%02d %02d:00:00",
                    F.col(year_col),
                    F.col(month_col),
                    F.col(day_col),
                    F.col(hour_col),
                ),
                "yyyy-MM-dd HH:mm:ss",
            ),
        )
    else:
        return out

    out = out.withColumn("date_utc", F.to_date(F.col(target_col)))
    out = out.withColumn("year", F.year(F.col(target_col)))
    out = out.withColumn("month", F.month(F.col(target_col)))
    out = out.withColumn("day", F.dayofmonth(F.col(target_col)))
    out = out.withColumn("hour", F.hour(F.col(target_col)))

    return out


# ------------------------------------------------------------------------------
# End-to-end convenience function
# ------------------------------------------------------------------------------

def standardize_core_units(
    df: DataFrame,
    *,
    wind_speed_col: str = "wind_speed",
    wind_speed_unit: str = "knots",
    temperature_col: str = "temperature",
    temperature_unit: str = "tenths_c",
    dew_point_col: str = "dew_point",
    dew_point_unit: str = "tenths_c",
    pressure_col: str = "sea_level_pressure",
    pressure_unit: str = "tenths_hpa",
    visibility_col: str = "visibility",
    visibility_unit: str = "m",
    ceiling_col: str = "ceiling_height",
    ceiling_unit: str = "m",
    timestamp_col: str = "timestamp",
) -> DataFrame:
    """
    Apply unit standardization for the core parsed weather fields.

    Expected canonical outputs:
    - wind_speed_ms
    - temperature_c
    - dew_point_c
    - sea_level_pressure_hpa
    - visibility_m
    - ceiling_height_m
    - timestamp_utc
    - date_utc, year, month, day, hour
    """
    out = df

    out = standardize_wind_speed(
        out,
        source_col=wind_speed_col,
        target_col="wind_speed_ms",
        source_unit=wind_speed_unit,
    )

    out = standardize_temperature(
        out,
        source_col=temperature_col,
        target_col="temperature_c",
        source_unit=temperature_unit,
    )

    out = standardize_dew_point(
        out,
        source_col=dew_point_col,
        target_col="dew_point_c",
        source_unit=dew_point_unit,
    )

    out = standardize_sea_level_pressure(
        out,
        source_col=pressure_col,
        target_col="sea_level_pressure_hpa",
        source_unit=pressure_unit,
    )

    out = standardize_visibility(
        out,
        source_col=visibility_col,
        target_col="visibility_m",
        source_unit=visibility_unit,
    )

    out = standardize_ceiling_height(
        out,
        source_col=ceiling_col,
        target_col="ceiling_height_m",
        source_unit=ceiling_unit,
    )

    out = normalize_timestamp(
        out,
        source_col=timestamp_col,
        target_col="timestamp_utc",
    )

    return out