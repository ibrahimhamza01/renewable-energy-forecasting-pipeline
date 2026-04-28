"""
Tests for src/physics/wind_power_curve.py

Run with:

    uv run pytest tests/test_wind_power_curve.py -v
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StructField, StructType

from src.physics.wind_power_curve import (
    DEFAULT_CUT_IN_SPEED_MS,
    DEFAULT_RATED_SPEED_MS,
    DEFAULT_CUT_OUT_SPEED_MS,
    add_wind_power_columns,
    classify_wind_power_class,
    compute_capacity_factor,
    compute_normalized_power,
    validate_power_curve_params,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[*]")
        .appName("test_wind_power_curve")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def _make_wind_df(spark, speeds):
    """Create a simple DataFrame with wind speeds."""
    rows = [(float(s),) if s is not None else (None,) for s in speeds]

    schema = StructType(
        [
            StructField("wind_speed_ms", DoubleType(), True),
        ]
    )

    return spark.createDataFrame(rows, schema=schema)


class TestParameterValidation:
    def test_valid_params_do_not_raise(self):
        validate_power_curve_params(3.5, 13.0, 25.0)

    def test_negative_cut_in_raises(self):
        with pytest.raises(ValueError):
            validate_power_curve_params(-1.0, 13.0, 25.0)

    def test_invalid_order_raises(self):
        with pytest.raises(ValueError):
            validate_power_curve_params(13.0, 3.5, 25.0)


class TestNormalizedPower:
    def test_zero_wind(self, spark):
        df = _make_wind_df(spark, [0.0])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] == 0.0

    def test_negative_wind_returns_null(self, spark):
        df = _make_wind_df(spark, [-1.0])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] is None

    def test_below_cut_in(self, spark):
        df = _make_wind_df(spark, [1.0, 2.0, 3.0])
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]
        assert all(p == 0.0 for p in powers)

    def test_at_cut_in(self, spark):
        df = _make_wind_df(spark, [DEFAULT_CUT_IN_SPEED_MS])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] == 0.0

    def test_between_cut_in_and_rated(self, spark):
        mid = (DEFAULT_CUT_IN_SPEED_MS + DEFAULT_RATED_SPEED_MS) / 2
        df = _make_wind_df(spark, [mid])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert 0.0 < power < 1.0

    def test_at_rated(self, spark):
        df = _make_wind_df(spark, [DEFAULT_RATED_SPEED_MS])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] == 1.0

    def test_above_rated_below_cut_out(self, spark):
        df = _make_wind_df(spark, [20.0])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] == 1.0

    def test_at_cut_out(self, spark):
        df = _make_wind_df(spark, [DEFAULT_CUT_OUT_SPEED_MS])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] == 1.0

    def test_above_cut_out(self, spark):
        df = _make_wind_df(spark, [30.0, 50.0])
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]
        assert all(p == 0.0 for p in powers)

    def test_null_wind(self, spark):
        df = _make_wind_df(spark, [None])
        result = compute_normalized_power(df)
        assert result.collect()[0]["normalized_power"] is None

    def test_monotonic_increase_before_rated(self, spark):
        speeds = [4.0, 6.0, 8.0, 10.0, 12.0]
        df = _make_wind_df(spark, speeds)
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]

        for i in range(1, len(powers)):
            assert powers[i] >= powers[i - 1]


class TestWindPowerColumns:
    def test_adds_expected_columns(self, spark):
        df = _make_wind_df(spark, [8.0])
        result = add_wind_power_columns(df)

        assert "normalized_power" in result.columns
        assert "wind_power_density_wm2" in result.columns

    def test_power_density_formula(self, spark):
        df = _make_wind_df(spark, [10.0])
        result = add_wind_power_columns(df)
        row = result.collect()[0]

        expected = 0.5 * 1.225 * (10.0**3)
        assert abs(row["wind_power_density_wm2"] - expected) < 0.1

    def test_negative_speed_density_is_null(self, spark):
        df = _make_wind_df(spark, [-2.0])
        result = add_wind_power_columns(df)
        assert result.collect()[0]["wind_power_density_wm2"] is None


class TestCapacityFactor:
    def test_overall_capacity_factor(self, spark):
        df = spark.createDataFrame(
            [(0.0,), (0.5,), (1.0,)],
            ["normalized_power"],
        )

        result = compute_capacity_factor(df)
        row = result.collect()[0]

        assert row["capacity_factor"] == 0.5
        assert row["observation_count"] == 3

    def test_grouped_capacity_factor(self, spark):
        df = spark.createDataFrame(
            [
                ("TX", 0.0, 5.0),
                ("TX", 1.0, 13.0),
                ("CA", 0.5, 8.0),
            ],
            ["state", "normalized_power", "wind_speed_ms"],
        )

        result = compute_capacity_factor(df, group_cols=["state"])
        rows = {row["state"]: row for row in result.collect()}

        assert rows["TX"]["capacity_factor"] == 0.5
        assert rows["TX"]["observation_count"] == 2
        assert rows["CA"]["capacity_factor"] == 0.5
        assert rows["CA"]["observation_count"] == 1


class TestWindPowerClass:
    def test_class_1(self, spark):
        df = spark.createDataFrame([(3.0,)], ["mean_wind_speed_ms"])
        result = classify_wind_power_class(df)
        assert result.collect()[0]["wind_power_class"] == 1

    def test_class_4(self, spark):
        df = spark.createDataFrame([(5.8,)], ["mean_wind_speed_ms"])
        result = classify_wind_power_class(df)
        assert result.collect()[0]["wind_power_class"] == 4

    def test_class_7(self, spark):
        df = spark.createDataFrame([(8.0,)], ["mean_wind_speed_ms"])
        result = classify_wind_power_class(df)
        assert result.collect()[0]["wind_power_class"] == 7

    def test_negative_class_is_null(self, spark):
        df = spark.createDataFrame([(-1.0,)], ["mean_wind_speed_ms"])
        result = classify_wind_power_class(df)
        assert result.collect()[0]["wind_power_class"] is None