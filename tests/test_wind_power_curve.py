"""
Tests for src/physics/wind_power_curve.py

Run with:
    cd ~/dats6450/renewable-energy-forecasting-pipeline
    export PROJECT_USER_CONFIG=configs/users/alejandro.yaml
    python3.10 -m pytest tests/test_wind_power_curve.py -v
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.physics.wind_power_curve import (
    compute_normalized_power,
    add_wind_power_columns,
    classify_wind_power_class,
    DEFAULT_CUT_IN_SPEED,
    DEFAULT_RATED_SPEED,
    DEFAULT_CUT_OUT_SPEED,
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
    return spark.createDataFrame(rows, ["wind_speed_ms"])


class TestNormalizedPower:
    """Test the normalized power curve function."""

    def test_zero_wind(self, spark):
        df = _make_wind_df(spark, [0.0])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert power == 0.0, "Zero wind should produce zero power"

    def test_below_cut_in(self, spark):
        df = _make_wind_df(spark, [1.0, 2.0, 3.0])
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]
        assert all(p == 0.0 for p in powers), "Below cut-in should be zero"

    def test_at_cut_in(self, spark):
        df = _make_wind_df(spark, [DEFAULT_CUT_IN_SPEED])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert power == 0.0, "At exactly cut-in, power should be 0"

    def test_at_rated(self, spark):
        df = _make_wind_df(spark, [DEFAULT_RATED_SPEED])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert abs(power - 1.0) < 0.001, "At rated speed, power should be ~1.0"

    def test_between_cut_in_and_rated(self, spark):
        mid = (DEFAULT_CUT_IN_SPEED + DEFAULT_RATED_SPEED) / 2
        df = _make_wind_df(spark, [mid])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert 0.0 < power < 1.0, "Mid-range should produce partial power"

    def test_above_rated_below_cut_out(self, spark):
        df = _make_wind_df(spark, [20.0])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert power == 1.0, "Between rated and cut-out should be 1.0"

    def test_at_cut_out(self, spark):
        df = _make_wind_df(spark, [DEFAULT_CUT_OUT_SPEED])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert power == 1.0, "At cut-out, should still be 1.0"

    def test_above_cut_out(self, spark):
        df = _make_wind_df(spark, [30.0, 50.0])
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]
        assert all(p == 0.0 for p in powers), "Above cut-out should be zero"

    def test_null_wind(self, spark):
        df = _make_wind_df(spark, [None])
        result = compute_normalized_power(df)
        power = result.collect()[0]["normalized_power"]
        assert power is None, "Null wind should produce null power"

    def test_monotonic_increase(self, spark):
        speeds = [4.0, 6.0, 8.0, 10.0, 12.0]
        df = _make_wind_df(spark, speeds)
        result = compute_normalized_power(df)
        powers = [row["normalized_power"] for row in result.collect()]
        for i in range(1, len(powers)):
            assert powers[i] >= powers[i - 1], "Power should increase with wind speed"


class TestWindPowerColumns:
    """Test the convenience function that adds all wind power columns."""

    def test_adds_both_columns(self, spark):
        df = _make_wind_df(spark, [8.0])
        result = add_wind_power_columns(df)
        assert "normalized_power" in result.columns
        assert "wind_power_density_wm2" in result.columns

    def test_power_density_formula(self, spark):
        df = _make_wind_df(spark, [10.0])
        result = add_wind_power_columns(df)
        row = result.collect()[0]
        # P = 0.5 * 1.225 * 10^3 = 612.5
        expected = 0.5 * 1.225 * (10.0 ** 3)
        assert abs(row["wind_power_density_wm2"] - expected) < 0.1

    def test_zero_speed_density(self, spark):
        df = _make_wind_df(spark, [0.0])
        result = add_wind_power_columns(df)
        row = result.collect()[0]
        assert row["wind_power_density_wm2"] == 0.0


class TestWindPowerClass:
    """Test NREL wind power classification."""

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
