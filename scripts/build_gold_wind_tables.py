"""
Layer 6: Build all gold wind tables from silver weather data.

This is the main entry point for Layer 6. It:
  1. Reads silver weather data from S3
  2. Filters to usable wind rows
  3. Applies the wind power curve (normalized power + power density)
  4. Builds gold tables at 4 grains:
     - Station hourly
     - Station daily
     - Region (state) daily
     - Region (state) monthly
  5. Writes all gold tables to S3

Usage:
    spark-submit ... scripts/build_gold_wind_tables.py

Requires:
    export PROJECT_USER_CONFIG=configs/users/alejandro.yaml
    export PYTHONPATH=$(pwd)
"""

from __future__ import annotations

from src.common.config import config
from src.common.paths import Paths
from src.common.spark_utils import get_spark_session
from src.physics.wind_power_curve import add_wind_power_columns
from src.physics.wind_indices import (
    build_station_hourly_wind,
    build_station_daily_wind,
    build_region_daily_wind,
    build_region_monthly_wind,
)
from src.storage.write_gold import write_gold


def main() -> None:
    spark = get_spark_session(app_name="layer6_build_gold_wind_tables")
    paths = Paths()

    # ------------------------------------------------------------------
    # 1. Read silver
    # ------------------------------------------------------------------
    print(f"Reading silver from: {paths.silver_weather}")
    silver_df = spark.read.parquet(paths.silver_weather)

    total_silver = silver_df.count()
    print(f"Silver rows: {total_silver:,}")

    # ------------------------------------------------------------------
    # 2. Filter to usable wind observations
    # ------------------------------------------------------------------
    wind_df = (
        silver_df
        .filter("is_wind_row_usable = true")
        .filter("has_valid_wind_speed = true")
        .filter("wind_speed_ms IS NOT NULL")
        .filter("wind_speed_ms >= 0")
        .filter("wind_speed_ms < 120")  # physical sanity cap
    )

    usable_count = wind_df.count()
    print(f"Usable wind rows: {usable_count:,} ({100*usable_count/total_silver:.1f}%)")

    # ------------------------------------------------------------------
    # 3. Apply wind power curve
    # ------------------------------------------------------------------
    print("Applying wind power curve...")
    wind_df = add_wind_power_columns(wind_df, wind_speed_col="wind_speed_ms")

    # ------------------------------------------------------------------
    # 4. Build gold tables at each grain
    # ------------------------------------------------------------------

    # Station hourly
    print("Building station hourly gold table...")
    station_hourly = build_station_hourly_wind(wind_df)
    write_gold(
        station_hourly,
        output_path=paths.gold_wind_station_hourly,
        partition_cols=["year", "state"],
    )

    # Station daily
    print("Building station daily gold table...")
    station_daily = build_station_daily_wind(wind_df)
    write_gold(
        station_daily,
        output_path=paths.gold_wind_station_daily,
        partition_cols=["year", "state"],
    )

    # Region daily
    print("Building region daily gold table...")
    region_daily = build_region_daily_wind(station_daily)
    write_gold(
        region_daily,
        output_path=paths.gold_wind_region_daily,
        partition_cols=["year", "state"],
    )

    # Region monthly
    print("Building region monthly gold table...")
    region_monthly = build_region_monthly_wind(region_daily)
    write_gold(
        region_monthly,
        output_path=paths.gold_wind_region_monthly,
        partition_cols=["year"],
    )

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print("\n=== Layer 6 Complete ===")
    print(f"Silver rows:          {total_silver:,}")
    print(f"Usable wind rows:     {usable_count:,}")
    print(f"Station hourly path:  {paths.gold_wind_station_hourly}")
    print(f"Station daily path:   {paths.gold_wind_station_daily}")
    print(f"Region daily path:    {paths.gold_wind_region_daily}")
    print(f"Region monthly path:  {paths.gold_wind_region_monthly}")

    spark.stop()


if __name__ == "__main__":
    main()
