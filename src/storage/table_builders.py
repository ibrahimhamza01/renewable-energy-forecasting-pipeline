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