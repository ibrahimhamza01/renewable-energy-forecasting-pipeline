import os
from pathlib import Path

import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.physics.wind_power_curve import add_wind_power_columns


def load_user_config() -> dict:
    config_path = os.environ.get("PROJECT_USER_CONFIG")
    if not config_path:
        raise RuntimeError("PROJECT_USER_CONFIG is not set")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"User config not found: {path}")

    with path.open("r") as f:
        return yaml.safe_load(f)


def s3_path(bucket: str, prefix: str) -> str:
    return f"s3a://{bucket}/{prefix.strip('/')}"


user_config = load_user_config()

project_bucket = user_config["aws"]["project_bucket"]
silver_prefix = user_config["aws"]["silver_prefix"]
silver_path = s3_path(project_bucket, silver_prefix)

spark = (
    SparkSession.builder
    .appName("layer6_partA_silver_smoke_test")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("Reading Silver data from logical config: aws.project_bucket + aws.silver_prefix")
print(f"Resolved Silver path: {silver_path}")

silver = spark.read.parquet(silver_path)

sample = (
    silver
    .select("station_id", "timestamp_utc", "state", "wind_speed_ms")
    .where(F.col("wind_speed_ms").isNotNull())
    .limit(10000)
)

result = add_wind_power_columns(sample)

result.select(
    "station_id",
    "timestamp_utc",
    "state",
    "wind_speed_ms",
    "normalized_power",
    "wind_power_density_wm2",
).show(30, truncate=False, vertical=True)

result.select(
    F.count("*").alias("rows"),
    F.min("wind_speed_ms").alias("min_wind_speed_ms"),
    F.max("wind_speed_ms").alias("max_wind_speed_ms"),
    F.min("normalized_power").alias("min_normalized_power"),
    F.max("normalized_power").alias("max_normalized_power"),
    F.avg("normalized_power").alias("avg_normalized_power"),
).show(truncate=False)

bad_rows = result.where(
    (F.col("normalized_power") < 0)
    | (F.col("normalized_power") > 1)
).count()

print(f"bad_normalized_power_rows={bad_rows}")

spark.stop()