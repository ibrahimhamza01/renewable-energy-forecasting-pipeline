from pyspark.sql import Row

from src.cleaning.standardize_units import (
    normalize_timestamp,
    standardize_ceiling_height,
    standardize_dew_point,
    standardize_sea_level_pressure,
    standardize_temperature,
    standardize_visibility,
    standardize_wind_speed,
)


def test_standardize_wind_speed_knots_to_ms(spark):
    df = spark.createDataFrame([
        Row(wind_speed=10.0),
    ])

    rows = standardize_wind_speed(
        df,
        source_col="wind_speed",
        target_col="wind_speed_ms",
        source_unit="knots",
    ).collect()

    assert abs(rows[0]["wind_speed_ms"] - 5.144) < 0.01


def test_standardize_wind_speed_passthrough_ms(spark):
    df = spark.createDataFrame([
        Row(wind_speed=5.1),
    ])

    rows = standardize_wind_speed(
        df,
        source_col="wind_speed",
        target_col="wind_speed_ms",
        source_unit="m/s",
    ).collect()

    assert float(rows[0]["wind_speed_ms"]) == 5.1


def test_standardize_temperature_from_tenths_c(spark):
    df = spark.createDataFrame([
        Row(temperature=93.0),
    ])

    rows = standardize_temperature(
        df,
        source_col="temperature",
        target_col="temperature_c",
        source_unit="tenths_c",
    ).collect()

    assert float(rows[0]["temperature_c"]) == 9.3


def test_standardize_dew_point_from_tenths_c(spark):
    df = spark.createDataFrame([
        Row(dew_point=78.0),
    ])

    rows = standardize_dew_point(
        df,
        source_col="dew_point",
        target_col="dew_point_c",
        source_unit="tenths_c",
    ).collect()

    assert float(rows[0]["dew_point_c"]) == 7.8


def test_standardize_pressure_from_tenths_hpa(spark):
    df = spark.createDataFrame([
        Row(sea_level_pressure=10132.0),
    ])

    rows = standardize_sea_level_pressure(
        df,
        source_col="sea_level_pressure",
        target_col="sea_level_pressure_hpa",
        source_unit="tenths_hpa",
    ).collect()

    assert float(rows[0]["sea_level_pressure_hpa"]) == 1013.2


def test_standardize_visibility_passthrough_meters(spark):
    df = spark.createDataFrame([
        Row(visibility=16093.0),
    ])

    rows = standardize_visibility(
        df,
        source_col="visibility",
        target_col="visibility_m",
        source_unit="m",
    ).collect()

    assert float(rows[0]["visibility_m"]) == 16093.0


def test_standardize_ceiling_height_feet_to_meters(spark):
    df = spark.createDataFrame([
        Row(ceiling_height=1000.0),
    ])

    rows = standardize_ceiling_height(
        df,
        source_col="ceiling_height",
        target_col="ceiling_height_m",
        source_unit="ft",
    ).collect()

    assert abs(rows[0]["ceiling_height_m"] - 304.8) < 0.01


def test_normalize_timestamp_from_iso_string(spark):
    df = spark.createDataFrame([
        Row(timestamp="2020-01-01T05:00:00"),
    ])

    rows = normalize_timestamp(
        df,
        source_col="timestamp",
        target_col="timestamp_utc",
    ).collect()

    assert str(rows[0]["timestamp_utc"]) == "2020-01-01 05:00:00"
    assert str(rows[0]["date_utc"]) == "2020-01-01"
    assert rows[0]["year"] == 2020
    assert rows[0]["month"] == 1
    assert rows[0]["day"] == 1
    assert rows[0]["hour"] == 5


def test_normalize_timestamp_from_parts(spark):
    df = spark.createDataFrame([
        Row(year=2020, month=1, day=2, hour=7),
    ])

    rows = normalize_timestamp(
        df,
        source_col="missing_timestamp_column",
        target_col="timestamp_utc",
        year_col="year",
        month_col="month",
        day_col="day",
        hour_col="hour",
    ).collect()

    assert str(rows[0]["timestamp_utc"]) == "2020-01-02 07:00:00"
    assert str(rows[0]["date_utc"]) == "2020-01-02"
    assert rows[0]["year"] == 2020
    assert rows[0]["month"] == 1
    assert rows[0]["day"] == 2
    assert rows[0]["hour"] == 7