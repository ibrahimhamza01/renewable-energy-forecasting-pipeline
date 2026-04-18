from pyspark.sql import Row

from src.cleaning.quality_filters import (
    QCSpec,
    apply_basic_consistency_checks,
    apply_qc_filter,
    apply_qc_filters,
    enforce_required_wind_fields,
    invalidate_out_of_range_values,
    nullify_sentinels,
)


def test_nullify_sentinels_on_canonical_columns(spark):
    df = spark.createDataFrame([
        Row(
            wind_speed_ms=9999.0,
            temperature_c=9999.0,
            dew_point_c=-9999.0,
            sea_level_pressure_hpa=99999.0,
            visibility_distance_m=999999.0,
            ceiling_height_m=99999.0,
            wind_direction_degrees=999.0,
        ),
        Row(
            wind_speed_ms=5.1,
            temperature_c=9.3,
            dew_point_c=7.8,
            sea_level_pressure_hpa=1013.2,
            visibility_distance_m=16093.0,
            ceiling_height_m=2200.0,
            wind_direction_degrees=324.0,
        ),
    ])

    sentinel_map = {
        "wind_speed_ms": {9999, 999.9},
        "temperature_c": {9999, 999.9, -9999, -999.9},
        "dew_point_c": {9999, 999.9, -9999, -999.9},
        "sea_level_pressure_hpa": {99999, 9999.9, 99999.9},
        "visibility_distance_m": {999999, 99999, 9999},
        "ceiling_height_m": {99999, 999999},
        "wind_direction_degrees": {999, 9999},
    }

    rows = nullify_sentinels(df, sentinel_map=sentinel_map).collect()

    assert rows[0]["wind_speed_ms"] is None
    assert rows[0]["temperature_c"] is None
    assert rows[0]["dew_point_c"] is None
    assert rows[0]["sea_level_pressure_hpa"] is None
    assert rows[0]["visibility_distance_m"] is None
    assert rows[0]["ceiling_height_m"] is None
    assert rows[0]["wind_direction_degrees"] is None

    assert float(rows[1]["wind_speed_ms"]) == 5.1
    assert float(rows[1]["temperature_c"]) == 9.3


def test_apply_qc_filter_nulls_invalid_value(spark):
    df = spark.createDataFrame([
        Row(wind_speed_ms=5.1, wind_speed_qc="1"),
        Row(wind_speed_ms=6.2, wind_speed_qc="3"),
    ])

    rows = apply_qc_filter(
        df,
        value_col="wind_speed_ms",
        qc_col="wind_speed_qc",
        allowed_flags=["1"],
    ).collect()

    assert float(rows[0]["wind_speed_ms"]) == 5.1
    assert rows[1]["wind_speed_ms"] is None


def test_apply_qc_filter_nulls_missing_qc_by_default(spark):
    df = spark.createDataFrame([
        Row(temperature_c=10.0, temperature_qc=None),
        Row(temperature_c=11.0, temperature_qc="1"),
    ])

    rows = apply_qc_filter(
        df,
        value_col="temperature_c",
        qc_col="temperature_qc",
        allowed_flags=["1"],
        null_when_qc_missing=True,
    ).collect()

    assert rows[0]["temperature_c"] is None
    assert float(rows[1]["temperature_c"]) == 11.0


def test_apply_qc_filters_multiple_fields(spark):
    df = spark.createDataFrame([
        Row(
            wind_speed_ms=5.0,
            wind_speed_qc="1",
            temperature_c=9.0,
            temperature_qc="3",
        )
    ])

    qc_specs = (
        QCSpec("wind_speed_ms", "wind_speed_qc", allowed_flags=("1",)),
        QCSpec("temperature_c", "temperature_qc", allowed_flags=("1",)),
    )

    rows = apply_qc_filters(df, qc_specs=qc_specs).collect()

    assert float(rows[0]["wind_speed_ms"]) == 5.0
    assert rows[0]["temperature_c"] is None


def test_invalidate_out_of_range_values_on_canonical_columns(spark):
    df = spark.createDataFrame([
        Row(
            wind_speed_ms=5.1,
            temperature_c=9.3,
            dew_point_c=7.8,
            sea_level_pressure_hpa=1013.2,
            visibility_distance_m=16093.0,
            ceiling_height_m=2200.0,
            wind_direction_degrees=324.0,
        ),
        Row(
            wind_speed_ms=120.0,
            temperature_c=80.0,
            dew_point_c=60.0,
            sea_level_pressure_hpa=1500.0,
            visibility_distance_m=-5.0,
            ceiling_height_m=50000.0,
            wind_direction_degrees=400.0,
        ),
    ])

    bounds = {
        "wind_direction_degrees": (0.0, 360.0),
        "wind_speed_ms": (0.0, 75.0),
        "temperature_c": (-90.0, 60.0),
        "dew_point_c": (-100.0, 50.0),
        "sea_level_pressure_hpa": (800.0, 1100.0),
        "visibility_distance_m": (0.0, 200000.0),
        "ceiling_height_m": (0.0, 30000.0),
    }

    rows = invalidate_out_of_range_values(df, bounds=bounds).collect()

    assert float(rows[0]["wind_speed_ms"]) == 5.1
    assert rows[1]["wind_speed_ms"] is None
    assert rows[1]["temperature_c"] is None
    assert rows[1]["dew_point_c"] is None
    assert rows[1]["sea_level_pressure_hpa"] is None
    assert rows[1]["visibility_distance_m"] is None
    assert rows[1]["ceiling_height_m"] is None
    assert rows[1]["wind_direction_degrees"] is None


def test_apply_basic_consistency_checks_nulls_dew_point_above_temperature(spark):
    df = spark.createDataFrame([
        Row(temperature_c=10.0, dew_point_c=8.0),
        Row(temperature_c=10.0, dew_point_c=12.0),
    ])

    rows = apply_basic_consistency_checks(df).collect()

    assert float(rows[0]["dew_point_c"]) == 8.0
    assert rows[1]["dew_point_c"] is None


def test_enforce_required_wind_fields_filters_unusable_rows(spark):
    df = spark.createDataFrame([
        Row(station_id="A", timestamp_utc="2020-01-01 00:00:00", wind_speed_ms=5.1),
        Row(station_id="B", timestamp_utc="2020-01-01 01:00:00", wind_speed_ms=None),
        Row(station_id="C", timestamp_utc=None, wind_speed_ms=6.2),
    ])

    filtered = enforce_required_wind_fields(
        df,
        require_speed=True,
        require_timestamp=True,
        timestamp_col="timestamp_utc",
    ).collect()

    assert len(filtered) == 1
    assert filtered[0]["station_id"] == "A"