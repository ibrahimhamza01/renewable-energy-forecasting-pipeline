from __future__ import annotations

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


def first_existing_col(df: DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(
        f"None of these columns exist: {candidates}\nAvailable columns: {df.columns}"
    )


def build_spark(spark_config: dict[str, Any], user_config: dict[str, Any]) -> SparkSession:
    spark_section = spark_config.get("spark", {})
    builder = (
        SparkSession.builder
        .appName(spark_section.get("app_name", "export-full-website-trends"))
        .master(deep_get(user_config, ["ec2", "spark_master_url"], spark_section.get("master", "local[*]")))
    )

    for key, value in spark_section.get("config", {}).items():
        builder = builder.config(key, str(value))

    return builder.getOrCreate()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    active_user_config = os.environ.get(
        "PROJECT_USER_CONFIG",
        "configs/users/syed.yaml",
    )

    user_config = load_yaml(repo_root / active_user_config)
    spark_config = load_yaml(repo_root / "configs/spark_config.yaml")
    paths_config = load_yaml(repo_root / "configs/paths.yaml")

    bucket = deep_get(user_config, ["aws", "project_bucket"])
    if not bucket:
        raise ValueError("Missing aws.project_bucket in active user config.")

    gold_region_daily_prefix = deep_get(paths_config, ["gold", "wind_region_daily"])
    if not gold_region_daily_prefix:
        raise ValueError("Missing gold.wind_region_daily in configs/paths.yaml.")

    gold_region_daily_path = s3_path(bucket, gold_region_daily_prefix)

    website_data_dir = repo_root / "website" / "public" / "data"
    website_data_dir.mkdir(parents=True, exist_ok=True)

    spark = build_spark(spark_config, user_config)

    print(f"Reading gold daily region table from: {gold_region_daily_path}")

    daily = spark.read.parquet(gold_region_daily_path)

    print("Gold daily columns:")
    print(daily.columns)

    date_col = first_existing_col(
        daily,
        ["date", "date_utc", "day", "observation_date"],
    )

    state_col = first_existing_col(
        daily,
        ["state", "region", "state_code"],
    )

    cf_col = first_existing_col(
        daily,
        [
            "capacity_factor",
            "daily_region_capacity_factor",
            "avg_capacity_factor",
            "mean_capacity_factor",
            "wind_capacity_factor",
        ],
    )

    daily_clean = (
        daily
        .withColumn("date", F.to_date(F.col(date_col)))
        .withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
        .withColumn(
            "season",
            F.when(F.col("month").isin(12, 1, 2), F.lit("winter"))
            .when(F.col("month").isin(3, 4, 5), F.lit("spring"))
            .when(F.col("month").isin(6, 7, 8), F.lit("summer"))
            .otherwise(F.lit("fall")),
        )
        .withColumn("state", F.col(state_col))
        .withColumn("capacity_factor", F.col(cf_col).cast("double"))
        .filter(F.col("date").isNotNull())
        .filter(F.col("year").between(1995, 2025))
        .filter(F.col("state").isNotNull())
        .filter(F.col("capacity_factor").isNotNull())
    )

    regional_trends = (
        daily_clean
        .groupBy("date", "year", "month", "season", "state")
        .agg(
            F.avg("capacity_factor").alias("capacity_factor"),
            F.count("*").alias("source_row_count"),
        )
        .orderBy("date", "state")
    )

    seasonal_trends = (
        daily_clean
        .groupBy("year", "season", "state")
        .agg(
            F.avg("capacity_factor").alias("capacity_factor"),
            F.countDistinct("date").alias("day_count"),
        )
        .orderBy("year", "state", "season")
    )

    regional_out = website_data_dir / "regional_trends.csv"
    seasonal_out = website_data_dir / "seasonal_trends.csv"

    regional_pdf = regional_trends.toPandas()
    seasonal_pdf = seasonal_trends.toPandas()

    regional_pdf.to_csv(regional_out, index=False)
    seasonal_pdf.to_csv(seasonal_out, index=False)

    print("\nExport complete.")
    print(f"Wrote: {regional_out}")
    print(f"Wrote: {seasonal_out}")
    print(f"regional rows: {len(regional_pdf):,}")
    print(f"seasonal rows: {len(seasonal_pdf):,}")

    if len(regional_pdf):
        print(f"years: {regional_pdf['year'].min()}–{regional_pdf['year'].max()}")
        print(f"states: {regional_pdf['state'].nunique()}")
        print(f"state list: {sorted(regional_pdf['state'].dropna().unique().tolist())}")

    spark.stop()


if __name__ == "__main__":
    main()