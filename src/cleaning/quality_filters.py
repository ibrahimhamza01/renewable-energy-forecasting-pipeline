# src/cleaning/quality_filters.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from pyspark.sql import DataFrame, Column
from pyspark.sql import functions as F


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

# IMPORTANT:
# NOAA ISD QC rules should ultimately be aligned with your project's
# data_contracts/quality_flag_rules.md.
#
# Until that contract is fully finalized, this module uses conservative defaults:
# - keep values only when QC is in an allowed set
# - convert known sentinels to null
# - remove implausible values using broad physical bounds
#
# Update these defaults once your team finalizes the exact QC policy.


DEFAULT_ALLOWED_QC_FLAGS = {"1", "5", "9", "A", "C", "I", "M"}

# Broad sentinels commonly seen in parsed NOAA-style encoded fields.
# These should be adjusted if your parser already strips some of them out.
DEFAULT_SENTINELS: dict[str, set] = {
    "wind_direction_deg": {999},
    "wind_speed": {9999, 999.9},
    "temperature_c": {9999, 999.9, -9999, -999.9},
    "dew_point_c": {9999, 999.9, -9999, -999.9},
    "sea_level_pressure_hpa": {99999, 9999.9, 99999.9},
    "visibility_m": {999999, 99999, 9999},
    "ceiling_height_m": {99999, 999999},
}

# Broad physical/plausibility bounds.
DEFAULT_NUMERIC_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "wind_direction_deg": (0.0, 360.0),
    "wind_speed": (0.0, 150.0),              # raw parsed speed before/after unit conversion
    "wind_speed_ms": (0.0, 75.0),            # very broad, but still physically meaningful
    "temperature_c": (-90.0, 60.0),
    "dew_point_c": (-100.0, 50.0),
    "sea_level_pressure_hpa": (800.0, 1100.0),
    "visibility_m": (0.0, 200000.0),
    "ceiling_height_m": (0.0, 30000.0),
}


@dataclass(frozen=True)
class QCSpec:
    """
    Defines how a measurement column should be filtered by its QC column.
    """
    value_col: str
    qc_col: str
    allowed_flags: Sequence[str] = field(default_factory=lambda: tuple(sorted(DEFAULT_ALLOWED_QC_FLAGS)))
    null_when_qc_missing: bool = True


# Conservative defaults for the core parsed fields you care about for Layer 3.
DEFAULT_QC_SPECS: tuple[QCSpec, ...] = (
    QCSpec("wind_speed", "wind_speed_qc"),
    QCSpec("wind_direction_deg", "wind_direction_qc"),
    QCSpec("temperature_c", "temperature_qc"),
    QCSpec("dew_point_c", "dew_point_qc"),
    QCSpec("sea_level_pressure_hpa", "sea_level_pressure_qc"),
    QCSpec("visibility_m", "visibility_qc"),
    QCSpec("ceiling_height_m", "ceiling_height_qc"),
)


# ------------------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------------------

def _trimmed_str(col_name: str) -> Column:
    return F.trim(F.col(col_name).cast("string"))


def _is_missing_string(col_name: str) -> Column:
    c = _trimmed_str(col_name)
    return (
        F.col(col_name).isNull()
        | (c == "")
        | F.upper(c).isin("NULL", "NONE", "NAN")
    )


def _nullify_if_in(col_name: str, sentinels: Iterable) -> Column:
    """
    Return a column expression that converts matching sentinel values to null.

    Handles both:
    - exact numeric matches (e.g. 9999.0 == 9999)
    - string-like matches after trimming/casting
    """
    sentinels = list(sentinels)
    if not sentinels:
        return F.col(col_name)

    numeric_sentinels = [x for x in sentinels if isinstance(x, (int, float))]
    string_sentinels = [str(x) for x in sentinels]

    numeric_match = F.lit(False)
    if numeric_sentinels:
        numeric_match = F.col(col_name).isin(*numeric_sentinels)

    string_match = _trimmed_str(col_name).isin(*string_sentinels)

    return F.when(
        F.col(col_name).isNull() | numeric_match | string_match,
        F.lit(None),
    ).otherwise(F.col(col_name))


def _within_bounds(col_name: str, min_value: float | None, max_value: float | None) -> Column:
    expr = F.lit(True)
    if min_value is not None:
        expr = expr & (F.col(col_name) >= F.lit(min_value))
    if max_value is not None:
        expr = expr & (F.col(col_name) <= F.lit(max_value))
    return expr


# ------------------------------------------------------------------------------
# Sentinel handling
# ------------------------------------------------------------------------------

def nullify_sentinels(
    df: DataFrame,
    sentinel_map: Mapping[str, Iterable] | None = None,
) -> DataFrame:
    """
    Convert configured sentinel values to null.

    Example:
        df = nullify_sentinels(
            df,
            {
                "wind_speed": {9999},
                "temperature_c": {9999, -9999},
            },
        )
    """
    sentinel_map = sentinel_map or DEFAULT_SENTINELS

    out = df
    for col_name, sentinels in sentinel_map.items():
        if col_name in out.columns:
            out = out.withColumn(col_name, _nullify_if_in(col_name, sentinels))

    return out


# ------------------------------------------------------------------------------
# QC filtering
# ------------------------------------------------------------------------------

def apply_qc_filter(
    df: DataFrame,
    value_col: str,
    qc_col: str,
    allowed_flags: Sequence[str] | None = None,
    null_when_qc_missing: bool = True,
) -> DataFrame:
    """
    Nullify a measurement column when its QC flag is not allowed.

    Rules:
    - if the value itself is null, leave it null
    - if QC is missing and null_when_qc_missing=True, null out the value
    - if QC is present but not in allowed_flags, null out the value
    """
    if value_col not in df.columns or qc_col not in df.columns:
        return df

    allowed_flags = tuple(allowed_flags or tuple(sorted(DEFAULT_ALLOWED_QC_FLAGS)))

    qc_clean = F.upper(_trimmed_str(qc_col))
    qc_is_missing = _is_missing_string(qc_col)
    qc_is_allowed = qc_clean.isin(*allowed_flags)

    if null_when_qc_missing:
        keep_expr = F.col(value_col).isNull() | qc_is_allowed
    else:
        keep_expr = F.col(value_col).isNull() | qc_is_allowed | qc_is_missing

    return df.withColumn(
        value_col,
        F.when(keep_expr, F.col(value_col)).otherwise(F.lit(None)),
    )


def apply_qc_filters(
    df: DataFrame,
    qc_specs: Sequence[QCSpec] | None = None,
) -> DataFrame:
    """
    Apply QC-based nullification across multiple fields.
    """
    qc_specs = qc_specs or DEFAULT_QC_SPECS

    out = df
    for spec in qc_specs:
        out = apply_qc_filter(
            out,
            value_col=spec.value_col,
            qc_col=spec.qc_col,
            allowed_flags=spec.allowed_flags,
            null_when_qc_missing=spec.null_when_qc_missing,
        )
    return out


# ------------------------------------------------------------------------------
# Plausibility / invalid-value filtering
# ------------------------------------------------------------------------------

def invalidate_out_of_range_values(
    df: DataFrame,
    bounds: Mapping[str, tuple[float | None, float | None]] | None = None,
) -> DataFrame:
    """
    Nullify values that fall outside configured numeric bounds.
    """
    bounds = bounds or DEFAULT_NUMERIC_BOUNDS

    out = df
    for col_name, (min_value, max_value) in bounds.items():
        if col_name not in out.columns:
            continue

        out = out.withColumn(
            col_name,
            F.when(
                F.col(col_name).isNull() | _within_bounds(col_name, min_value, max_value),
                F.col(col_name),
            ).otherwise(F.lit(None)),
        )

    return out


def apply_basic_consistency_checks(df: DataFrame) -> DataFrame:
    """
    Apply cross-field consistency checks.

    Current checks:
    - dew point should not exceed temperature by a meaningful amount
    - zero wind speed with a non-null direction is allowed (calm conditions may still encode oddly),
      so we do not force direction null here
    """
    out = df

    if {"temperature_c", "dew_point_c"}.issubset(set(out.columns)):
        out = out.withColumn(
            "dew_point_c",
            F.when(
                F.col("dew_point_c").isNull()
                | F.col("temperature_c").isNull()
                | (F.col("dew_point_c") <= F.col("temperature_c") + F.lit(0.5)),
                F.col("dew_point_c"),
            ).otherwise(F.lit(None)),
        )

    return out


# ------------------------------------------------------------------------------
# Wind-focused utilities
# ------------------------------------------------------------------------------

def enforce_required_wind_fields(
    df: DataFrame,
    require_speed: bool = True,
    require_timestamp: bool = False,
    timestamp_col: str = "timestamp_utc",
) -> DataFrame:
    """
    Filter rows down to those usable for wind modeling.

    Recommended usage:
    - run this after sentinel handling, QC filtering, and unit standardization
    - prefer using wind_speed_ms if available, otherwise fall back to wind_speed
    """
    out = df

    speed_col = "wind_speed_ms" if "wind_speed_ms" in out.columns else "wind_speed"

    conditions = []
    if require_speed and speed_col in out.columns:
        conditions.append(F.col(speed_col).isNotNull())

    if require_timestamp and timestamp_col in out.columns:
        conditions.append(F.col(timestamp_col).isNotNull())

    if not conditions:
        return out

    combined = conditions[0]
    for cond in conditions[1:]:
        combined = combined & cond

    return out.filter(combined)


# ------------------------------------------------------------------------------
# End-to-end convenience function for Layer 3 Part A
# ------------------------------------------------------------------------------

def clean_core_weather_fields(
    df: DataFrame,
    *,
    sentinel_map: Mapping[str, Iterable] | None = None,
    qc_specs: Sequence[QCSpec] | None = None,
    bounds: Mapping[str, tuple[float | None, float | None]] | None = None,
) -> DataFrame:
    """
    Main cleaning pass for parsed NOAA ISD weather fields.

    Order matters:
    1. sentinel -> null
    2. QC enforcement
    3. range validation
    4. cross-field consistency checks
    """
    out = df
    out = nullify_sentinels(out, sentinel_map=sentinel_map)
    out = apply_qc_filters(out, qc_specs=qc_specs)
    out = invalidate_out_of_range_values(out, bounds=bounds)
    out = apply_basic_consistency_checks(out)
    return out


# ------------------------------------------------------------------------------
# Optional diagnostics helpers
# ------------------------------------------------------------------------------

def add_quality_audit_columns(df: DataFrame) -> DataFrame:
    """
    Add simple audit columns to help with notebook validation/debugging.

    This does not change the business columns; it only adds summary flags.
    """
    out = df

    if "wind_speed_ms" in out.columns:
        out = out.withColumn("is_wind_row_usable", F.col("wind_speed_ms").isNotNull())
    elif "wind_speed" in out.columns:
        out = out.withColumn("is_wind_row_usable", F.col("wind_speed").isNotNull())

    if {"temperature_c", "dew_point_c"}.issubset(set(out.columns)):
        out = out.withColumn(
            "temp_dew_consistent",
            F.when(
                F.col("temperature_c").isNull() | F.col("dew_point_c").isNull(),
                F.lit(None),
            ).otherwise(F.col("dew_point_c") <= F.col("temperature_c") + F.lit(0.5)),
        )

    return out