"""
Layer 6 Part B: Gold wind table builder.

Reads Silver weather data, builds wind potential tables at multiple grains,
and writes Gold outputs.

No S3 paths are hardcoded here.
All paths must be passed in by the caller.
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.physics.wind_indices import (
    build_daily_region_wind_potential,
    build_daily_station_wind_potential,
    build_hourly_station_wind_potential,
    build_monthly_region_wind_summary,
)
from src.storage.write_gold import (
    write_daily_region_wind_gold,
    write_daily_station_wind_gold,
    write_hourly_station_wind_gold,
    write_monthly_region_wind_gold,
)


def build_wind_gold_tables_from_silver_df(
    silver_df,
    min_hourly_obs_per_day: int = 6,
    min_daily_obs_per_month: int = 15,
):
    """
    Build all Layer 6 wind Gold DataFrames from a Silver DataFrame.

    This function does not write anything.
    It is useful for sample validation before full-scale Gold writes.
    """

    silver_required = (
        silver_df
        .select(
            "station_id",
            "timestamp_utc",
            "date_utc",
            "year",
            "month",
            "state",
            "wind_speed_ms",
        )
        .where(F.col("wind_speed_ms").isNotNull())
    )

    hourly_station = build_hourly_station_wind_potential(silver_required)

    daily_station = build_daily_station_wind_potential(
        hourly_station,
        min_hourly_obs_per_day=min_hourly_obs_per_day,
    )

    daily_region = build_daily_region_wind_potential(daily_station)

    monthly_region = build_monthly_region_wind_summary(
        daily_region,
        min_daily_obs_per_month=min_daily_obs_per_month,
    )

    return {
        "hourly_station": hourly_station,
        "daily_station": daily_station,
        "daily_region": daily_region,
        "monthly_region": monthly_region,
    }


def write_wind_gold_tables(
    tables: dict,
    gold_hourly_station_path: str,
    gold_daily_station_path: str,
    gold_daily_region_path: str,
    gold_monthly_region_path: str,
) -> None:
    """
    Write all wind Gold DataFrames to their resolved output paths.
    """

    write_hourly_station_wind_gold(
        tables["hourly_station"],
        gold_hourly_station_path,
    )

    write_daily_station_wind_gold(
        tables["daily_station"],
        gold_daily_station_path,
    )

    write_daily_region_wind_gold(
        tables["daily_region"],
        gold_daily_region_path,
    )

    write_monthly_region_wind_gold(
        tables["monthly_region"],
        gold_monthly_region_path,
    )


def build_and_write_wind_gold_tables(
    spark: SparkSession,
    silver_weather_path: str,
    gold_hourly_station_path: str,
    gold_daily_station_path: str,
    gold_daily_region_path: str,
    gold_monthly_region_path: str,
    min_hourly_obs_per_day: int = 6,
    min_daily_obs_per_month: int = 15,
) -> None:
    """
    Full production builder.

    Reads full Silver weather table, builds all Layer 6 wind Gold tables,
    and writes outputs to resolved Gold paths.
    """

    silver = spark.read.parquet(silver_weather_path)

    tables = build_wind_gold_tables_from_silver_df(
        silver,
        min_hourly_obs_per_day=min_hourly_obs_per_day,
        min_daily_obs_per_month=min_daily_obs_per_month,
    )

    write_wind_gold_tables(
        tables=tables,
        gold_hourly_station_path=gold_hourly_station_path,
        gold_daily_station_path=gold_daily_station_path,
        gold_daily_region_path=gold_daily_region_path,
        gold_monthly_region_path=gold_monthly_region_path,
    )

# ---------------------------------------------------------------------
# Layer 7 Part B: Final analytical Gold table builders
# ---------------------------------------------------------------------


def add_season_column(df, month_col: str = "month"):
    """
    Add meteorological season label from month.

    Seasons:
        winter = Dec, Jan, Feb
        spring = Mar, Apr, May
        summer = Jun, Jul, Aug
        fall   = Sep, Oct, Nov
    """

    return df.withColumn(
        "season",
        F.when(F.col(month_col).isin(12, 1, 2), F.lit("winter"))
        .when(F.col(month_col).isin(3, 4, 5), F.lit("spring"))
        .when(F.col(month_col).isin(6, 7, 8), F.lit("summer"))
        .when(F.col(month_col).isin(9, 10, 11), F.lit("fall"))
        .otherwise(F.lit(None)),
    )


def build_gold_monthly_state_wind(region_monthly_df):
    """
    Build final Layer 7 monthly state-level analytical wind table.

    Source:
        gold/wind/region/monthly

    Output table:
        gold_monthly_state_wind

    Grain:
        one row per state-year-month

    Purpose:
        - strongest states
        - seasonal wind potential
        - long-run monthly reporting
        - presentation-ready descriptive analysis
    """

    required_cols = [
        "state",
        "year",
        "month",
        "monthly_region_capacity_factor",
        "monthly_mean_wind_speed_ms",
        "min_daily_region_capacity_factor",
        "max_daily_region_capacity_factor",
        "daily_observation_count",
        "avg_station_count",
        "is_valid_monthly_region_index",
        "wind_power_class",
    ]

    df = region_monthly_df.select(*required_cols)

    df = add_season_column(df, month_col="month")

    df = df.withColumn(
        "capacity_factor_range",
        F.col("max_daily_region_capacity_factor")
        - F.col("min_daily_region_capacity_factor"),
    )

    df = df.withColumn(
        "is_high_wind_month",
        F.col("monthly_region_capacity_factor") >= F.lit(0.075),
    )

    df = df.withColumn(
        "is_low_wind_month",
        F.col("monthly_region_capacity_factor") <= F.lit(0.020),
    )

    return df.select(
        "state",
        "year",
        "month",
        "season",
        "monthly_region_capacity_factor",
        "monthly_mean_wind_speed_ms",
        "min_daily_region_capacity_factor",
        "max_daily_region_capacity_factor",
        "capacity_factor_range",
        "daily_observation_count",
        "avg_station_count",
        "is_valid_monthly_region_index",
        "wind_power_class",
        "is_high_wind_month",
        "is_low_wind_month",
    )

def build_gold_daily_region_wind(region_daily_df):
    """
    Build final Layer 7 daily state-level analytical wind table.

    Source:
        gold/wind/region/daily

    Output table:
        gold_daily_region_wind

    Grain:
        one row per state-date

    Purpose:
        - daily wind potential analysis
        - stability and volatility analysis
        - extreme high/low wind day detection
        - ML base table source
    """

    required_cols = [
        "state",
        "year",
        "month",
        "date_utc",
        "daily_region_capacity_factor",
        "mean_region_wind_speed_ms",
        "avg_station_wind_speed_std_ms",
        "avg_station_min_wind_speed_ms",
        "avg_station_max_wind_speed_ms",
        "station_count",
        "total_hourly_observations",
    ]

    df = region_daily_df.select(*required_cols)

    df = add_season_column(df, month_col="month")

    df = df.withColumn(
        "daily_wind_speed_range_ms",
        F.col("avg_station_max_wind_speed_ms")
        - F.col("avg_station_min_wind_speed_ms"),
    )

    df = df.withColumn(
        "is_low_wind_day",
        F.col("daily_region_capacity_factor") <= F.lit(0.01),
    )

    df = df.withColumn(
        "is_high_wind_day",
        F.col("daily_region_capacity_factor") >= F.lit(0.10),
    )

    return df.select(
        "state",
        "date_utc",
        "year",
        "month",
        "season",
        "daily_region_capacity_factor",
        "mean_region_wind_speed_ms",
        "avg_station_wind_speed_std_ms",
        "avg_station_min_wind_speed_ms",
        "avg_station_max_wind_speed_ms",
        "daily_wind_speed_range_ms",
        "station_count",
        "total_hourly_observations",
        "is_low_wind_day",
        "is_high_wind_day",
    )

def build_gold_extreme_event_windows(gold_daily_region_df):
    """
    Build final Layer 7 extreme wind event table.

    Source:
        gold_daily_region_wind

    Output table:
        gold_extreme_event_windows

    Grain:
        one row per state-date
    """

    state_thresholds = (
        gold_daily_region_df
        .groupBy("state")
        .agg(
            F.expr("percentile_approx(daily_region_capacity_factor, 0.10)").alias(
                "state_low_wind_threshold"
            ),
            F.expr("percentile_approx(daily_region_capacity_factor, 0.90)").alias(
                "state_high_wind_threshold"
            ),
            F.avg("daily_region_capacity_factor").alias("state_avg_capacity_factor"),
            F.stddev("daily_region_capacity_factor").alias("state_std_capacity_factor_raw"),
        )
        .withColumn(
            "state_std_capacity_factor",
            F.when(
                F.col("state_std_capacity_factor_raw") < F.lit(1e-6),
                F.lit(None),
            ).otherwise(F.col("state_std_capacity_factor_raw")),
        )
        .drop("state_std_capacity_factor_raw")
    )

    df = gold_daily_region_df.join(
        state_thresholds,
        on="state",
        how="left",
    )

    df = df.withColumn(
        "is_extreme_low_wind_day",
        F.col("daily_region_capacity_factor") <= F.col("state_low_wind_threshold"),
    )

    df = df.withColumn(
        "is_extreme_high_wind_day",
        F.col("daily_region_capacity_factor") >= F.col("state_high_wind_threshold"),
    )

    df = df.withColumn(
        "capacity_factor_z_score",
        F.when(
            F.col("state_std_capacity_factor").isNull(),
            F.lit(None),
        ).otherwise(
            (F.col("daily_region_capacity_factor") - F.col("state_avg_capacity_factor"))
            / F.col("state_std_capacity_factor")
        ),
    )

    df = df.withColumn(
        "is_extreme_event_day",
        F.col("is_extreme_low_wind_day") | F.col("is_extreme_high_wind_day"),
    )

    df = df.withColumn(
        "extreme_event_type",
        F.when(F.col("is_extreme_low_wind_day"), F.lit("low_wind"))
        .when(F.col("is_extreme_high_wind_day"), F.lit("high_wind"))
        .otherwise(F.lit("normal")),
    )

    return df.select(
        "state",
        "date_utc",
        "year",
        "month",
        "season",
        "daily_region_capacity_factor",
        "mean_region_wind_speed_ms",
        "station_count",
        "total_hourly_observations",
        "state_low_wind_threshold",
        "state_high_wind_threshold",
        "state_avg_capacity_factor",
        "state_std_capacity_factor",
        "capacity_factor_z_score",
        "is_extreme_low_wind_day",
        "is_extreme_high_wind_day",
        "is_extreme_event_day",
        "extreme_event_type",
    )