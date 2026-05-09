from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml
from pyspark.sql import SparkSession, DataFrame, functions as F


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def deep_get(d: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def s3_path(bucket: str, prefix: str) -> str:
    return f"s3a://{bucket}/{prefix.strip('/')}"


def build_spark(spark_config: dict[str, Any], user_config: dict[str, Any]) -> SparkSession:
    spark_section = spark_config.get("spark", {})
    builder = (
        SparkSession.builder
        .appName("export-additional-website-gold-artifacts")
        .master(deep_get(user_config, ["ec2", "spark_master_url"], spark_section.get("master", "local[*]")))
    )

    for key, value in spark_section.get("config", {}).items():
        builder = builder.config(key, str(value))

    return builder.getOrCreate()


def first_existing_col(df: DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(f"Missing expected columns. Tried {candidates}. Available: {df.columns}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    active_user_config = os.environ.get("PROJECT_USER_CONFIG", "configs/users/syed.yaml")

    user_config = load_yaml(repo_root / active_user_config)
    spark_config = load_yaml(repo_root / "configs/spark_config.yaml")
    paths_config = load_yaml(repo_root / "configs/paths.yaml")

    bucket = deep_get(user_config, ["aws", "project_bucket"])
    if not bucket:
        raise ValueError("Missing aws.project_bucket")

    website_data_dir = repo_root / "website" / "public" / "data"
    website_data_dir.mkdir(parents=True, exist_ok=True)

    spark = build_spark(spark_config, user_config)

    region_daily_path = s3_path(bucket, deep_get(paths_config, ["gold", "wind_region_daily"]))
    region_monthly_path = s3_path(bucket, deep_get(paths_config, ["gold", "wind_region_monthly"]))
    station_daily_path = s3_path(bucket, deep_get(paths_config, ["gold", "wind_station_daily"]))

    print(f"Reading region daily: {region_daily_path}")
    region_daily = spark.read.parquet(region_daily_path)

    print(f"Reading region monthly: {region_monthly_path}")
    region_monthly = spark.read.parquet(region_monthly_path)

    print(f"Reading station daily: {station_daily_path}")
    station_daily = spark.read.parquet(station_daily_path)

    daily_date_col = first_existing_col(region_daily, ["date_utc", "date", "day"])
    daily_state_col = first_existing_col(region_daily, ["state", "region", "state_code"])
    daily_cf_col = first_existing_col(region_daily, ["daily_region_capacity_factor", "capacity_factor"])
    daily_wind_col = first_existing_col(region_daily, ["mean_region_wind_speed_ms", "avg_wind_speed_ms", "wind_speed_ms"])

    daily = (
        region_daily
        .withColumn("date", F.to_date(F.col(daily_date_col)))
        .withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
        .withColumn("state", F.col(daily_state_col))
        .withColumn("capacity_factor", F.col(daily_cf_col).cast("double"))
        .withColumn("mean_wind_speed_ms", F.col(daily_wind_col).cast("double"))
        .filter(F.col("year").between(1995, 2025))
    )

    yearly_state_summary = (
        daily
        .groupBy("year", "state")
        .agg(
            F.avg("capacity_factor").alias("avg_capacity_factor"),
            F.avg("mean_wind_speed_ms").alias("avg_wind_speed_ms"),
            F.countDistinct("date").alias("day_count"),
        )
        .orderBy("year", "state")
    )

    state_wind_summary = (
        daily
        .groupBy("state")
        .agg(
            F.avg("capacity_factor").alias("avg_capacity_factor"),
            F.avg("mean_wind_speed_ms").alias("avg_wind_speed_ms"),
            F.min("year").alias("first_year"),
            F.max("year").alias("last_year"),
            F.countDistinct("date").alias("day_count"),
        )
        .orderBy(F.desc("avg_capacity_factor"))
    )

    monthly_date_col = first_existing_col(region_monthly, ["month", "month_utc"])
    monthly_state_col = first_existing_col(region_monthly, ["state", "region", "state_code"])
    monthly_cf_col = first_existing_col(region_monthly, ["monthly_region_capacity_factor", "capacity_factor", "avg_capacity_factor"])

    if "year" in region_monthly.columns:
        monthly = region_monthly.withColumn("year", F.col("year"))
    else:
        monthly = region_monthly.withColumn("year", F.year(F.to_date(F.col(monthly_date_col))))

    monthly_state_trends = (
        monthly
        .withColumn("state", F.col(monthly_state_col))
        .withColumn("month", F.col(monthly_date_col).cast("int"))
        .withColumn("capacity_factor", F.col(monthly_cf_col).cast("double"))
        .filter(F.col("year").between(1995, 2025))
        .select("year", "month", "state", "capacity_factor")
        .orderBy("year", "month", "state")
    )

    station_id_col = first_existing_col(station_daily, ["station_id", "STATION", "station"])
    station_state_col = first_existing_col(station_daily, ["state", "region", "state_code"])
    station_wind_col = first_existing_col(station_daily, ["mean_wind_speed_ms", "avg_wind_speed_ms", "wind_speed_ms"])
    station_cf_col = first_existing_col(station_daily, ["daily_capacity_factor", "capacity_factor", "avg_capacity_factor"])

    lat_col = "latitude" if "latitude" in station_daily.columns else None
    lon_col = "longitude" if "longitude" in station_daily.columns else None

    station_base = (
        station_daily
        .withColumn("station_id", F.col(station_id_col))
        .withColumn("state", F.col(station_state_col))
        .withColumn("avg_wind_speed_ms", F.col(station_wind_col).cast("double"))
        .withColumn("capacity_factor", F.col(station_cf_col).cast("double"))
    )

    agg_exprs = [
        F.avg("avg_wind_speed_ms").alias("avg_wind_speed_ms"),
        F.avg("capacity_factor").alias("avg_capacity_factor"),
        F.count("*").alias("daily_row_count"),
    ]

    if lat_col:
        station_base = station_base.withColumn("latitude", F.col(lat_col).cast("double"))
        agg_exprs.append(F.first("latitude", ignorenulls=True).alias("latitude"))

    if lon_col:
        station_base = station_base.withColumn("longitude", F.col(lon_col).cast("double"))
        agg_exprs.append(F.first("longitude", ignorenulls=True).alias("longitude"))

    top_wind_stations = (
        station_base
        .groupBy("station_id", "state")
        .agg(*agg_exprs)
        .orderBy(F.desc("avg_wind_speed_ms"))
        .limit(250)
    )

    yearly_state_summary.toPandas().to_csv(website_data_dir / "yearly_state_summary.csv", index=False)
    state_wind_summary.toPandas().to_csv(website_data_dir / "state_wind_summary.csv", index=False)
    monthly_state_trends.toPandas().to_csv(website_data_dir / "monthly_state_trends.csv", index=False)
    top_wind_stations.toPandas().to_csv(website_data_dir / "top_wind_stations.csv", index=False)

    summary = {
        "historical_window": {
            "start_year": int(daily.agg(F.min("year")).collect()[0][0]),
            "end_year": int(daily.agg(F.max("year")).collect()[0][0]),
        },
        "coverage": {
            "states": int(daily.select("state").distinct().count()),
            "daily_region_rows": int(daily.count()),
            "station_daily_rows": int(station_daily.count()),
            "top_station_export_rows": int(top_wind_stations.count()),
        },
        "source_tables": {
            "region_daily": region_daily_path,
            "region_monthly": region_monthly_path,
            "station_daily": station_daily_path,
        },
    }

    with open(website_data_dir / "pipeline_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Additional website gold artifacts exported.")
    print(json.dumps(summary, indent=2))

    spark.stop()


if __name__ == "__main__":
    main()