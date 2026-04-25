"""
Layer 6 Part B: Wind index generation at multiple grains.

Transforms silver hourly weather data into gold wind energy tables at
four aggregation levels:
  - Station hourly (with power curve applied)
  - Station daily
  - Region daily
  - Region/state monthly

All functions expect a silver DataFrame that has already been filtered
to usable wind rows and enriched with wind power columns.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_station_hourly_wind(df: DataFrame) -> DataFrame:
    """
    Gold: station-level hourly wind potential.

    This is essentially the silver table filtered to usable wind rows
    with power curve columns added. Serves as the base for all higher
    aggregations.

    Expected input columns:
      station_id, timestamp_utc, date_utc, year, month, day, hour,
      state, region, station_name, latitude, longitude, elevation_m,
      wind_speed_ms, wind_direction_degrees, temperature_c,
      normalized_power, wind_power_density_wm2
    """
    return df.select(
        "station_id",
        "station_name",
        "state",
        "region",
        F.col("LATITUDE").cast("double").alias("latitude"),
        F.col("LONGITUDE").cast("double").alias("longitude"),
        "elevation_m",
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
        "normalized_power",
        "wind_power_density_wm2",
    )


def build_station_daily_wind(df: DataFrame) -> DataFrame:
    """
    Gold: station-level daily wind potential aggregation.

    Aggregates hourly station data to daily summaries.
    """
    return (
        df.groupBy(
            "station_id",
            "station_name",
            "state",
            "region",
            "date_utc",
            "year",
            "month",
            "day",
        )
        .agg(
            F.round(F.avg("wind_speed_ms"), 4).alias("mean_wind_speed_ms"),
            F.round(F.max("wind_speed_ms"), 4).alias("max_wind_speed_ms"),
            F.round(F.min("wind_speed_ms"), 4).alias("min_wind_speed_ms"),
            F.round(F.stddev("wind_speed_ms"), 4).alias("std_wind_speed_ms"),
            F.round(F.avg("normalized_power"), 6).alias("capacity_factor"),
            F.round(F.avg("wind_power_density_wm2"), 4).alias("mean_wind_power_density_wm2"),
            F.round(F.max("wind_power_density_wm2"), 4).alias("max_wind_power_density_wm2"),
            F.round(F.avg("temperature_c"), 4).alias("mean_temperature_c"),
            F.round(F.avg("sea_level_pressure_hpa"), 4).alias("mean_pressure_hpa"),
            F.count("wind_speed_ms").alias("observation_count"),
            # Wind direction — circular mean not trivial, so take mode-like approach
            F.round(F.avg(
                F.sin(F.radians(F.col("wind_direction_degrees").cast("double")))
            ), 6).alias("sin_mean_direction"),
            F.round(F.avg(
                F.cos(F.radians(F.col("wind_direction_degrees").cast("double")))
            ), 6).alias("cos_mean_direction"),
        )
        .withColumn(
            "mean_wind_direction_degrees",
            F.round(
                (F.degrees(F.atan2(F.col("sin_mean_direction"), F.col("cos_mean_direction"))) + 360) % 360,
                1,
            ),
        )
        .drop("sin_mean_direction", "cos_mean_direction")
    )


def build_region_daily_wind(station_daily_df: DataFrame) -> DataFrame:
    """
    Gold: region-level (state) daily wind potential.

    Aggregates station daily data to state/region daily summaries.
    """
    return (
        station_daily_df.groupBy(
            "state",
            "region",
            "date_utc",
            "year",
            "month",
            "day",
        )
        .agg(
            F.round(F.avg("mean_wind_speed_ms"), 4).alias("mean_wind_speed_ms"),
            F.round(F.max("max_wind_speed_ms"), 4).alias("max_wind_speed_ms"),
            F.round(F.avg("capacity_factor"), 6).alias("capacity_factor"),
            F.round(F.avg("mean_wind_power_density_wm2"), 4).alias("mean_wind_power_density_wm2"),
            F.round(F.max("max_wind_power_density_wm2"), 4).alias("max_wind_power_density_wm2"),
            F.round(F.avg("mean_temperature_c"), 4).alias("mean_temperature_c"),
            F.round(F.avg("mean_pressure_hpa"), 4).alias("mean_pressure_hpa"),
            F.sum("observation_count").alias("total_observations"),
            F.countDistinct("station_id").alias("station_count"),
        )
    )


def build_region_monthly_wind(region_daily_df: DataFrame) -> DataFrame:
    """
    Gold: region-level (state) monthly wind potential.

    Aggregates region daily data to monthly summaries.
    """
    return (
        region_daily_df.groupBy(
            "state",
            "region",
            "year",
            "month",
        )
        .agg(
            F.round(F.avg("mean_wind_speed_ms"), 4).alias("mean_wind_speed_ms"),
            F.round(F.max("max_wind_speed_ms"), 4).alias("max_wind_speed_ms"),
            F.round(F.avg("capacity_factor"), 6).alias("capacity_factor"),
            F.round(F.avg("mean_wind_power_density_wm2"), 4).alias("mean_wind_power_density_wm2"),
            F.round(F.max("max_wind_power_density_wm2"), 4).alias("max_wind_power_density_wm2"),
            F.round(F.avg("mean_temperature_c"), 4).alias("mean_temperature_c"),
            F.sum("total_observations").alias("total_observations"),
            F.round(F.avg("station_count"), 0).cast("int").alias("avg_station_count"),
            F.count("date_utc").alias("days_in_period"),
        )
    )
