"""
Layer 6 Part A: Wind power curve and theoretical power logic.

Implements a generic normalized wind turbine power curve that converts
wind speed (m/s) into normalized power output (0.0 to 1.0) and capacity
factor estimates.

The power curve follows standard wind energy engineering:
  - Below cut-in speed: no power (turbine idle)
  - Cut-in to rated speed: cubic power increase (P ~ v^3)
  - Rated to cut-out speed: constant rated power (1.0)
  - Above cut-out speed: no power (turbine shut down for safety)

Reference turbine defaults are based on typical modern utility-scale
wind turbines (e.g., Vestas V90-2.0, GE 1.5sle class).
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


# ---------------------------------------------------------------------------
# Default turbine parameters (m/s)
# ---------------------------------------------------------------------------
DEFAULT_CUT_IN_SPEED = 3.5      # m/s — turbine starts generating
DEFAULT_RATED_SPEED = 13.0      # m/s — turbine reaches max output
DEFAULT_CUT_OUT_SPEED = 25.0    # m/s — turbine shuts down for safety


def compute_normalized_power(
    df: DataFrame,
    wind_speed_col: str = "wind_speed_ms",
    output_col: str = "normalized_power",
    cut_in: float = DEFAULT_CUT_IN_SPEED,
    rated: float = DEFAULT_RATED_SPEED,
    cut_out: float = DEFAULT_CUT_OUT_SPEED,
) -> DataFrame:
    """
    Apply a normalized wind turbine power curve to a DataFrame.

    Returns a value between 0.0 and 1.0:
      - 0.0 = no power output
      - 1.0 = rated (maximum) power output

    The cubic region uses: ((v - cut_in) / (rated - cut_in))^3

    Parameters
    ----------
    df : DataFrame
        Must contain a wind speed column in m/s.
    wind_speed_col : str
        Name of the wind speed column.
    output_col : str
        Name of the output normalized power column.
    cut_in : float
        Cut-in wind speed (m/s).
    rated : float
        Rated wind speed (m/s).
    cut_out : float
        Cut-out wind speed (m/s).

    Returns
    -------
    DataFrame with the new normalized power column added.
    """
    v = F.col(wind_speed_col)

    cubic_fraction = ((v - F.lit(cut_in)) / F.lit(rated - cut_in)) ** 3

    power_expr = (
        F.when(v.isNull(), None)
        .when(v < F.lit(cut_in), 0.0)
        .when(v < F.lit(rated), cubic_fraction)
        .when(v <= F.lit(cut_out), 1.0)
        .otherwise(0.0)  # above cut-out
    )

    return df.withColumn(output_col, F.round(power_expr, 6))


def compute_capacity_factor(
    df: DataFrame,
    power_col: str = "normalized_power",
    group_cols: list[str] | None = None,
    output_col: str = "capacity_factor",
) -> DataFrame:
    """
    Compute capacity factor as the mean normalized power over a group.

    Capacity factor = mean(normalized_power) over the group.
    A capacity factor of 0.30 means the turbine produced 30% of its
    theoretical maximum output over the period.

    Parameters
    ----------
    df : DataFrame
        Must contain a normalized power column.
    power_col : str
        Name of the normalized power column.
    group_cols : list[str] or None
        Columns to group by. If None, computes overall capacity factor.
    output_col : str
        Name of the output capacity factor column.

    Returns
    -------
    Aggregated DataFrame with capacity factor.
    """
    if group_cols is None:
        return df.agg(
            F.round(F.avg(power_col), 6).alias(output_col),
            F.count(power_col).alias("observation_count"),
        )

    return (
        df.groupBy(*group_cols)
        .agg(
            F.round(F.avg(power_col), 6).alias(output_col),
            F.count(power_col).alias("observation_count"),
            F.round(F.avg("wind_speed_ms"), 4).alias("mean_wind_speed_ms"),
            F.round(F.stddev("wind_speed_ms"), 4).alias("std_wind_speed_ms"),
            F.round(F.min("wind_speed_ms"), 4).alias("min_wind_speed_ms"),
            F.round(F.max("wind_speed_ms"), 4).alias("max_wind_speed_ms"),
        )
    )


def classify_wind_power_class(
    df: DataFrame,
    wind_speed_col: str = "mean_wind_speed_ms",
    output_col: str = "wind_power_class",
) -> DataFrame:
    """
    Classify locations into NREL wind power classes (1-7) based on
    mean wind speed at the observation height.

    NREL Wind Power Classification (approximate, at 10m height):
      Class 1: < 4.4 m/s  (Poor)
      Class 2: 4.4 - 5.1  (Marginal)
      Class 3: 5.1 - 5.6  (Fair)
      Class 4: 5.6 - 6.0  (Good)
      Class 5: 6.0 - 6.4  (Excellent)
      Class 6: 6.4 - 7.0  (Outstanding)
      Class 7: >= 7.0     (Superb)
    """
    v = F.col(wind_speed_col)

    class_expr = (
        F.when(v.isNull(), None)
        .when(v < 4.4, 1)
        .when(v < 5.1, 2)
        .when(v < 5.6, 3)
        .when(v < 6.0, 4)
        .when(v < 6.4, 5)
        .when(v < 7.0, 6)
        .otherwise(7)
    )

    return df.withColumn(output_col, class_expr)


def add_wind_power_columns(
    df: DataFrame,
    wind_speed_col: str = "wind_speed_ms",
    cut_in: float = DEFAULT_CUT_IN_SPEED,
    rated: float = DEFAULT_RATED_SPEED,
    cut_out: float = DEFAULT_CUT_OUT_SPEED,
) -> DataFrame:
    """
    Convenience function: add normalized_power and wind_power_density
    columns to an hourly weather DataFrame.

    Wind power density (W/m^2) = 0.5 * rho * v^3
    where rho = 1.225 kg/m^3 (standard air density at sea level)
    """
    AIR_DENSITY = 1.225  # kg/m^3

    df = compute_normalized_power(
        df,
        wind_speed_col=wind_speed_col,
        output_col="normalized_power",
        cut_in=cut_in,
        rated=rated,
        cut_out=cut_out,
    )

    v = F.col(wind_speed_col)

    df = df.withColumn(
        "wind_power_density_wm2",
        F.when(v.isNull(), None)
        .otherwise(F.round(F.lit(0.5) * F.lit(AIR_DENSITY) * (v ** 3), 4)),
    )

    return df
