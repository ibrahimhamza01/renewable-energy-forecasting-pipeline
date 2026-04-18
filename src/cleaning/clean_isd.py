# src/cleaning/clean_isd.py

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.cleaning.quality_filters import (
    QCSpec,
    add_quality_audit_columns,
    apply_basic_consistency_checks,
    apply_qc_filter,
    enforce_required_wind_fields,
    invalidate_out_of_range_values,
    nullify_sentinels,
)


DEFAULT_REQUIRED_INPUT_COLUMNS: tuple[str, ...] = (
    "station_id",
)

DEFAULT_EXPECTED_OUTPUT_COLUMNS: tuple[str, ...] = (
    "station_id",
    "timestamp_utc",
    "date_utc",
    "year",
    "month",
    "day",
    "hour",
    "wind_speed_ms",
    "wind_direction_degrees",
    "temperature_c",
    "dew_point_c",
    "sea_level_pressure_hpa",
    "visibility_distance_m",
    "ceiling_height_m",
)

DEFAULT_CORE_ANALYSIS_COLUMNS: tuple[str, ...] = (
    "station_id",
    "timestamp_utc",
    "wind_speed_ms",
)


def validate_required_columns(
    df: DataFrame,
    required_columns: Sequence[str] | None = None,
) -> None:
    required_columns = tuple(required_columns or DEFAULT_REQUIRED_INPUT_COLUMNS)
    missing = [col_name for col_name in required_columns if col_name not in df.columns]

    if missing:
        raise ValueError(
            "Input DataFrame is missing required columns for clean_isd.py: "
            + ", ".join(missing)
        )


def build_parsed_sentinel_map() -> dict[str, set]:
    """
    Sentinel map aligned to the Layer 2 parsed schema.

    These defaults are conservative. Tighten them later if your project's
    quality flag contract defines more precise behavior.
    """
    return {
        "wind_direction_degrees": {999, 9999},
        "wind_speed_ms": {9999, 999.9},
        "temperature_c": {9999, 999.9, -9999, -999.9},
        "dew_point_c": {9999, 999.9, -9999, -999.9},
        "sea_level_pressure_hpa": {99999, 9999.9, 99999.9},
        "visibility_distance_m": {999999, 99999, 9999},
        "ceiling_height_m": {99999, 999999},
    }


def build_parsed_bounds() -> dict[str, tuple[float | None, float | None]]:
    """
    Broad plausibility bounds for already-standardized parsed columns.
    """
    return {
        "wind_direction_degrees": (0.0, 360.0),
        "wind_speed_ms": (0.0, 75.0),
        "temperature_c": (-90.0, 60.0),
        "dew_point_c": (-100.0, 50.0),
        "sea_level_pressure_hpa": (800.0, 1100.0),
        "visibility_distance_m": (0.0, 200000.0),
        "ceiling_height_m": (0.0, 30000.0),
    }


def build_parsed_qc_specs() -> tuple[QCSpec, ...]:
    """
    QC filtering aligned to the Layer 2 parsed schema.
    """
    return (
        QCSpec("wind_speed_ms", "wind_speed_qc"),
        QCSpec("wind_direction_degrees", "wind_direction_qc"),
        QCSpec("temperature_c", "temperature_qc"),
        QCSpec("dew_point_c", "dew_point_qc"),
        QCSpec("sea_level_pressure_hpa", "sea_level_pressure_qc"),
        QCSpec("visibility_distance_m", "visibility_distance_qc"),
        QCSpec("ceiling_height_m", "ceiling_height_qc"),
    )


def drop_duplicate_observations(
    df: DataFrame,
    subset: Sequence[str] | None = None,
) -> DataFrame:
    if subset is None:
        default_subset = [c for c in ("station_id", "timestamp_utc") if c in df.columns]
        subset = default_subset if default_subset else None

    if subset:
        return df.dropDuplicates(list(subset))

    return df.dropDuplicates()


def drop_rows_missing_core_fields(
    df: DataFrame,
    required_columns: Sequence[str] | None = None,
) -> DataFrame:
    required_columns = tuple(required_columns or DEFAULT_CORE_ANALYSIS_COLUMNS)
    existing_required = [c for c in required_columns if c in df.columns]

    if not existing_required:
        return df

    return df.dropna(subset=existing_required)


def add_time_columns(
    df: DataFrame,
    timestamp_col: str = "timestamp_utc",
) -> DataFrame:
    """
    Add standard calendar columns from an existing normalized timestamp column.
    Ensures timestamp_utc is stored as a Spark timestamp.
    """
    if timestamp_col not in df.columns:
        return df

    out = df.withColumn(
        timestamp_col,
        F.to_timestamp(F.col(timestamp_col), "yyyy-MM-dd'T'HH:mm:ss")
    )

    out = out.withColumn("date_utc", F.to_date(F.col(timestamp_col)))
    out = out.withColumn("year", F.year(F.col(timestamp_col)))
    out = out.withColumn("month", F.month(F.col(timestamp_col)))
    out = out.withColumn("day", F.dayofmonth(F.col(timestamp_col)))
    out = out.withColumn("hour", F.hour(F.col(timestamp_col)))
    return out


def add_cleaning_flags(df: DataFrame) -> DataFrame:
    out = df

    if "wind_speed_ms" in out.columns:
        out = out.withColumn(
            "has_valid_wind_speed",
            F.col("wind_speed_ms").isNotNull(),
        )

    if "timestamp_utc" in out.columns:
        out = out.withColumn(
            "has_valid_timestamp",
            F.col("timestamp_utc").isNotNull(),
        )

    if {"station_id", "timestamp_utc"}.issubset(set(out.columns)):
        out = out.withColumn(
            "is_core_row_complete",
            F.col("station_id").isNotNull()
            & F.col("timestamp_utc").isNotNull(),
        )

    return out


def apply_qc_filters_parsed(
    df: DataFrame,
    qc_specs: Sequence[QCSpec],
) -> DataFrame:
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


def clean_isd_dataframe(
    df: DataFrame,
    *,
    sentinel_map: Mapping[str, Iterable] | None = None,
    qc_specs: Sequence[QCSpec] | None = None,
    bounds: Mapping[str, tuple[float | None, float | None]] | None = None,
    timestamp_col: str = "timestamp_utc",
    require_wind_speed: bool = True,
    require_timestamp: bool = True,
    drop_duplicate_rows: bool = True,
    add_audit_columns: bool = True,
    drop_rows_missing_core: bool = True,
) -> DataFrame:
    """
    End-to-end Layer 3 cleaning pipeline for already-parsed NOAA ISD rows.

    Expected input schema is the Layer 2 parsed schema, where units are already
    standardized for the core weather fields.
    """
    validate_required_columns(df)

    out = df

    effective_sentinel_map = sentinel_map or build_parsed_sentinel_map()
    effective_qc_specs = qc_specs or build_parsed_qc_specs()
    effective_bounds = bounds or build_parsed_bounds()

    # 1. Clean canonical parsed fields
    out = nullify_sentinels(out, sentinel_map=effective_sentinel_map)
    out = apply_qc_filters_parsed(out, qc_specs=effective_qc_specs)
    out = invalidate_out_of_range_values(out, bounds=effective_bounds)

    # 2. Cross-field consistency checks
    out = apply_basic_consistency_checks(out)

    # 3. Derive date/time helper columns from timestamp_utc
    out = add_time_columns(out, timestamp_col=timestamp_col)

    # 4. Wind-focused usability filter
    out = enforce_required_wind_fields(
        out,
        require_speed=require_wind_speed,
        require_timestamp=require_timestamp,
        timestamp_col=timestamp_col,
    )

    if drop_duplicate_rows:
        out = drop_duplicate_observations(out)

    if add_audit_columns:
        out = add_quality_audit_columns(out)
        out = add_cleaning_flags(out)

    if drop_rows_missing_core:
        out = drop_rows_missing_core_fields(out)

    return out


def clean_isd_dataframe_minimal(df: DataFrame) -> DataFrame:
    return clean_isd_dataframe(df)


def clean_isd_dataframe_with_defaults(df: DataFrame) -> DataFrame:
    return clean_isd_dataframe(df)


def finalize_cleaned_weather_table(
    df: DataFrame,
    keep_extra_columns: bool = True,
) -> DataFrame:
    out = df

    key_first = [c for c in DEFAULT_EXPECTED_OUTPUT_COLUMNS if c in out.columns]
    remaining = [c for c in df.columns if c not in key_first]

    if keep_extra_columns:
        ordered = key_first + remaining
    else:
        ordered = key_first

    return out.select(*ordered)


def build_cleaned_weather_table(
    parsed_df: DataFrame,
    *,
    keep_extra_columns: bool = True,
    sentinel_map: Mapping[str, Iterable] | None = None,
    qc_specs: Sequence[QCSpec] | None = None,
    bounds: Mapping[str, tuple[float | None, float | None]] | None = None,
    timestamp_col: str = "timestamp_utc",
    require_wind_speed: bool = True,
    require_timestamp: bool = True,
    add_audit_columns: bool = True,
) -> DataFrame:
    cleaned = clean_isd_dataframe(
        parsed_df,
        sentinel_map=sentinel_map,
        qc_specs=qc_specs,
        bounds=bounds,
        timestamp_col=timestamp_col,
        require_wind_speed=require_wind_speed,
        require_timestamp=require_timestamp,
        add_audit_columns=add_audit_columns,
    )

    return finalize_cleaned_weather_table(
        cleaned,
        keep_extra_columns=keep_extra_columns,
    )