import os
from pathlib import Path

import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.physics.wind_indices import (
    build_hourly_station_wind_potential,
    build_daily_station_wind_potential,
    build_daily_region_wind_potential,
    build_monthly_region_wind_summary,
)


def load_user_config():
    path = os.environ["PROJECT_USER_CONFIG"]
    with open(path, "r") as f:
        return yaml.safe_load(f)


def s3_path(bucket, prefix):
    return f"s3a://{bucket}/{prefix.strip('/')}"


config = load_user_config()

silver_path = s3_path(
    config["aws"]["project_bucket"],
    config["aws"]["silver_prefix"],
)

spark = (
    SparkSession.builder
    .appName("test_wind_indices_sample")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# -----------------------------
# Load SMALL sample from Silver
# -----------------------------
silver = spark.read.parquet(silver_path)

sample = (
    silver
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
    .limit(50000)
)

print("Sample loaded")

# -----------------------------
# Hourly
# -----------------------------
hourly = build_hourly_station_wind_potential(sample)

print("Hourly schema:")
hourly.printSchema()

# -----------------------------
# Daily station
# -----------------------------
daily_station = build_daily_station_wind_potential(hourly)

print("Daily station sample:")
daily_station.show(5, truncate=False)

# -----------------------------
# Daily region
# -----------------------------
daily_region = build_daily_region_wind_potential(daily_station)

print("Daily region sample:")
daily_region.show(5, truncate=False)

# -----------------------------
# Monthly region
# -----------------------------
monthly = build_monthly_region_wind_summary(daily_region)

print("Monthly region sample:")
monthly.show(5, truncate=False)

# -----------------------------
# Basic validation
# -----------------------------
print("Validation:")

print("Hourly count:", hourly.count())
print("Daily station count:", daily_station.count())
print("Daily region count:", daily_region.count())
print("Monthly count:", monthly.count())

spark.stop()
