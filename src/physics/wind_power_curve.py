"""
Layer 6 Part A: Wind power curve and theoretical power logic.

This module converts wind speed in meters per second into normalized wind
energy potential values using a simplified turbine-like power curve.

The curve behavior is:

- below cut-in speed: 0.0
- cut-in to rated speed: cubic ramp
- rated to cut-out speed: 1.0
- above cut-out speed: 0.0
- null or negative wind speed: null

This module is Spark-safe and avoids Python UDFs.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


DEFAULT_CUT_IN_SPEED_MS = 3.5
DEFAULT_RATED_SPEED_MS = 13.0
DEFAULT_CUT_OUT_SPEED_MS = 25.0
DEFAULT_AIR_DENSITY_KG_M3 = 1.225


def validate_power_curve_params(
    cut_in: float,
    rated: float,
    cut_out: float,
) -> None:
    """Validate turbine power-curve speed thresholds."""
    if cut_in < 0:
        raise ValueError("cut_in must be non-negative")

    if not cut_in < rated < cut_out:
        raise ValueError("Expected cut_in < rated < cut_out")


def compute_normalized_power(
    df: DataFrame,
    wind_speed_col: str = "wind_speed_ms",
    output_col: str = "normalized_power",
    cut_in: float = DEFAULT_CUT_IN_SPEED_MS,
    rated: float = DEFAULT_RATED_SPEED_MS,
    cut_out: float = DEFAULT_CUT_OUT_SPEED_MS,
) -> DataFrame:
    """
    Add normalized turbine-like power output to a Spark DataFrame.

    The cubic ramp uses:

        (v^3 - cut_in^3) / (rated^3 - cut_in^3)

    This better reflects the physical relationship P ~ v^3 while still
    normalizing output to the interval [0, 1].
    """
    validate_power_curve_params(cut_in=cut_in, rated=rated, cut_out=cut_out)

    v = F.col(wind_speed_col).cast("double")

    cubic_fraction = (
        (F.pow(v, 3) - F.lit(cut_in**3))
        / F.lit(rated**3 - cut_in**3)
    )

    power_expr = (
        F.when(v.isNull(), F.lit(None).cast("double"))
        .when(v < 0, F.lit(None).cast("double"))
        .when(v < F.lit(cut_in), F.lit(0.0))
        .when(v < F.lit(rated), cubic_fraction)
        .when(v <= F.lit(cut_out), F.lit(1.0))
        .otherwise(F.lit(0.0))
    )

    return df.withColumn(output_col, F.round(power_expr, 6))


def add_wind_power_columns(
    df: DataFrame,
    wind_speed_col: str = "wind_speed_ms",
    cut_in: float = DEFAULT_CUT_IN_SPEED_MS,
    rated: float = DEFAULT_RATED_SPEED_MS,
    cut_out: float = DEFAULT_CUT_OUT_SPEED_MS,
    air_density_kg_m3: float = DEFAULT_AIR_DENSITY_KG_M3,
) -> DataFrame:
    """
    Add normalized power and wind power density columns.

    Wind power density:

        0.5 * air_density * wind_speed^3

    Output columns:

    - normalized_power
    - wind_power_density_wm2
    """
    validate_power_curve_params(cut_in=cut_in, rated=rated, cut_out=cut_out)

    df = compute_normalized_power(
        df=df,
        wind_speed_col=wind_speed_col,
        output_col="normalized_power",
        cut_in=cut_in,
        rated=rated,
        cut_out=cut_out,
    )

    v = F.col(wind_speed_col).cast("double")

    density_expr = (
        F.when(v.isNull(), F.lit(None).cast("double"))
        .when(v < 0, F.lit(None).cast("double"))
        .otherwise(F.lit(0.5) * F.lit(air_density_kg_m3) * F.pow(v, 3))
    )

    return df.withColumn(
        "wind_power_density_wm2",
        F.round(density_expr, 4),
    )


def compute_capacity_factor(
    df: DataFrame,
    power_col: str = "normalized_power",
    group_cols: list[str] | None = None,
    output_col: str = "capacity_factor",
) -> DataFrame:
    """
    Compute capacity factor as mean normalized power.
    """
    if group_cols is None:
        return df.agg(
            F.round(F.avg(power_col), 6).alias(output_col),
            F.count(power_col).alias("observation_count"),
        )

    agg_exprs = [
        F.round(F.avg(power_col), 6).alias(output_col),
        F.count(power_col).alias("observation_count"),
    ]

    if "wind_speed_ms" in df.columns:
        agg_exprs.extend(
            [
                F.round(F.avg("wind_speed_ms"), 4).alias("mean_wind_speed_ms"),
                F.round(F.stddev("wind_speed_ms"), 4).alias("std_wind_speed_ms"),
                F.round(F.min("wind_speed_ms"), 4).alias("min_wind_speed_ms"),
                F.round(F.max("wind_speed_ms"), 4).alias("max_wind_speed_ms"),
            ]
        )

    return df.groupBy(*group_cols).agg(*agg_exprs)


def classify_wind_power_class(
    df: DataFrame,
    wind_speed_col: str = "mean_wind_speed_ms",
    output_col: str = "wind_power_class",
) -> DataFrame:
    """
    Classify wind resource quality using approximate NREL-style wind speed classes.
    """
    v = F.col(wind_speed_col).cast("double")

    class_expr = (
        F.when(v.isNull(), F.lit(None).cast("int"))
        .when(v < 0, F.lit(None).cast("int"))
        .when(v < 4.4, F.lit(1))
        .when(v < 5.1, F.lit(2))
        .when(v < 5.6, F.lit(3))
        .when(v < 6.0, F.lit(4))
        .when(v < 6.4, F.lit(5))
        .when(v < 7.0, F.lit(6))
        .otherwise(F.lit(7))
    )

    return df.withColumn(output_col, class_expr)