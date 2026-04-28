"""
Layer 6 Part B: Wind index generation.

This module builds wind potential datasets at multiple grains from the
validated Silver weather table.

It assumes the input Silver table contains:

- station_id
- timestamp_utc
- date_utc
- year
- month
- state
- wind_speed_ms
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.physics.wind_power_curve import (
    add_wind_power_columns,
    classify_wind_power_class,
    compute_capacity_factor,
)


def build_hourly_station_wind_potential(df: DataFrame) -> DataFrame:
    """
    Build hourly station-level wind potential.

    Output grain:
        station_id + timestamp_utc
    """
    required_cols = [
        "station_id",
        "timestamp_utc",
        "date_utc",
        "year",
        "month",
        "state",
        "wind_speed_ms",
    ]

    selected = df.select(*required_cols)

    with_power = add_wind_power_columns(
        selected,
        wind_speed_col="wind_speed_ms",
    )

    return with_power.select(
        "station_id",
        "timestamp_utc",
        "date_utc",
        "year",
        "month",
        "state",
        "wind_speed_ms",
        "normalized_power",
        "wind_power_density_wm2",
    )


def build_daily_station_wind_potential(
    hourly_df: DataFrame,
    min_hourly_obs_per_day: int = 6,
) -> DataFrame:
    """
    Build daily station-level wind potential.

    Output grain:
        station_id + date_utc
    """
    daily = compute_capacity_factor(
        hourly_df,
        power_col="normalized_power",
        group_cols=["station_id", "date_utc", "year", "month", "state"],
        output_col="daily_capacity_factor",
    )

    daily = daily.withColumnRenamed(
        "observation_count",
        "hourly_observation_count",
    )

    daily = daily.withColumn(
        "is_valid_daily_station_index",
        F.col("hourly_observation_count") >= F.lit(min_hourly_obs_per_day),
    )

    return classify_wind_power_class(
        daily,
        wind_speed_col="mean_wind_speed_ms",
        output_col="wind_power_class",
    )


def build_daily_region_wind_potential(
    daily_station_df: DataFrame,
) -> DataFrame:
    """
    Build daily state/region-level wind potential.

    Current region grain:
        state + date_utc
    """
    return (
        daily_station_df
        .where(F.col("is_valid_daily_station_index") == F.lit(True))
        .groupBy("state", "date_utc", "year", "month")
        .agg(
            F.round(F.avg("daily_capacity_factor"), 6).alias(
                "daily_region_capacity_factor"
            ),
            F.round(F.avg("mean_wind_speed_ms"), 4).alias(
                "mean_region_wind_speed_ms"
            ),
            F.round(F.avg("std_wind_speed_ms"), 4).alias(
                "avg_station_wind_speed_std_ms"
            ),
            F.round(F.avg("min_wind_speed_ms"), 4).alias(
                "avg_station_min_wind_speed_ms"
            ),
            F.round(F.avg("max_wind_speed_ms"), 4).alias(
                "avg_station_max_wind_speed_ms"
            ),
            F.countDistinct("station_id").alias("station_count"),
            F.sum("hourly_observation_count").alias("total_hourly_observations"),
        )
    )


def build_monthly_region_wind_summary(
    daily_region_df: DataFrame,
    min_daily_obs_per_month: int = 15,
) -> DataFrame:
    """
    Build monthly state/region-level wind summaries.

    Current region grain:
        state + year + month
    """
    monthly = (
        daily_region_df
        .groupBy("state", "year", "month")
        .agg(
            F.round(F.avg("daily_region_capacity_factor"), 6).alias(
                "monthly_region_capacity_factor"
            ),
            F.round(F.avg("mean_region_wind_speed_ms"), 4).alias(
                "monthly_mean_wind_speed_ms"
            ),
            F.round(F.min("daily_region_capacity_factor"), 6).alias(
                "min_daily_region_capacity_factor"
            ),
            F.round(F.max("daily_region_capacity_factor"), 6).alias(
                "max_daily_region_capacity_factor"
            ),
            F.count("*").alias("daily_observation_count"),
            F.round(F.avg("station_count"), 2).alias("avg_station_count"),
        )
    )

    monthly = monthly.withColumn(
        "is_valid_monthly_region_index",
        F.col("daily_observation_count") >= F.lit(min_daily_obs_per_month),
    )

    return classify_wind_power_class(
        monthly,
        wind_speed_col="monthly_mean_wind_speed_ms",
        output_col="wind_power_class",
    )