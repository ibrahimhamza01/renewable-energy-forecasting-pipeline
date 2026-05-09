from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml
from pyspark.sql import SparkSession, functions as F


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
        .appName("export-final-gbt-website-artifacts")
        .master(deep_get(user_config, ["ec2", "spark_master_url"], spark_section.get("master", "local[*]")))
    )

    for key, value in spark_section.get("config", {}).items():
        builder = builder.config(key, str(value))

    return builder.getOrCreate()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    active_user_config = os.environ.get("PROJECT_USER_CONFIG", "configs/users/syed.yaml")

    user_config = load_yaml(repo_root / active_user_config)
    spark_config = load_yaml(repo_root / "configs/spark_config.yaml")
    paths_config = load_yaml(repo_root / "configs/paths.yaml")

    bucket = deep_get(user_config, ["aws", "project_bucket"])

    website_data_dir = repo_root / "website" / "public" / "data"
    website_data_dir.mkdir(parents=True, exist_ok=True)

    spark = build_spark(spark_config, user_config)

    forecast_path = (
        f"s3a://{bucket}/forecasts/outputs/"
        "run_id=20260504T090915Z/"
        "model_version=final_tuned_gbt_20260504T063157Z"
    )

    ml_base_path = s3_path(bucket, deep_get(paths_config, ["gold", "wind_ml_base"]))

    print(f"Reading forecasts: {forecast_path}")
    forecasts = spark.read.parquet(forecast_path)

    print(f"Reading ML base actuals: {ml_base_path}")
    actuals = spark.read.parquet(ml_base_path)

    forecast_clean = (
        forecasts
        .select(
            F.col("forecast_date").alias("date"),
            F.col("state"),
            F.col("prediction").cast("double").alias("prediction"),
            F.col("model_name"),
            F.col("generation_timestamp"),
            F.col("horizon_days"),
        )
    )

    actual_clean = (
        actuals
        .select(
            F.col("date_utc").alias("date"),
            F.col("state"),
            F.col("daily_region_capacity_factor").cast("double").alias("current_capacity_factor"),
            F.col("next_day_daily_region_capacity_factor").cast("double").alias("actual"),
            F.col("mean_region_wind_speed_ms").cast("double").alias("mean_region_wind_speed_ms"),
            F.col("season"),
            F.col("year"),
        )
    )

    joined = (
        forecast_clean
        .join(actual_clean, on=["date", "state"], how="inner")
        .filter(F.col("actual").isNotNull())
        .filter(F.col("prediction").isNotNull())
        .withColumn("error", F.col("prediction") - F.col("actual"))
        .withColumn("absolute_error", F.abs(F.col("error")))
        .select(
            F.col("date").cast("string").alias("date"),
            "state",
            "season",
            "year",
            "current_capacity_factor",
            "actual",
            "prediction",
            "error",
            "absolute_error",
            "mean_region_wind_speed_ms",
            "model_name",
            "horizon_days",
        )
        .orderBy("date", "state")
    )

    joined.toPandas().to_csv(website_data_dir / "forecast_vs_actual.csv", index=False)

    metrics = joined.agg(
        F.sqrt(F.avg(F.pow(F.col("prediction") - F.col("actual"), 2))).alias("rmse"),
        F.avg(F.abs(F.col("prediction") - F.col("actual"))).alias("mae"),
        F.avg(F.col("prediction") - F.col("actual")).alias("bias"),
        F.count("*").alias("evaluation_rows"),
        F.min("date").alias("start_date"),
        F.max("date").alias("end_date"),
        F.countDistinct("state").alias("states"),
    ).collect()[0]

    model_metrics = {
        "final_model_name": "final_tuned_gbt",
        "model_family": "Spark MLlib Gradient-Boosted Trees",
        "target": "next_day_daily_region_capacity_factor",
        "metrics": {
            "rmse": float(metrics["rmse"]),
            "mae": float(metrics["mae"]),
            "bias": float(metrics["bias"]),
            "evaluation_rows": int(metrics["evaluation_rows"]),
        },
        "coverage": {
            "start_date": str(metrics["start_date"]),
            "end_date": str(metrics["end_date"]),
            "states": int(metrics["states"]),
        },
        "source": {
            "forecast_outputs": forecast_path,
            "ml_base_actuals": ml_base_path,
            "model_registry": f"s3a://{bucket}/models/registry/final_gbt/stages/",
        },
    }

    with open(website_data_dir / "model_metrics.json", "w") as f:
        json.dump(model_metrics, f, indent=2)

    # Proxy feature importance for now. Actual Spark GBT importances can be extracted
    # from the model pipeline later, but this is enough for website artifact display.
    feature_candidates = [
        "mean_region_wind_speed_ms",
        "avg_station_wind_speed_std_ms",
        "daily_wind_speed_range_ms",
        "station_count",
        "total_hourly_observations",
        "cf_lag_1d",
        "cf_lag_2d",
        "cf_lag_3d",
        "cf_lag_7d",
        "cf_rolling_3d_mean",
        "cf_rolling_7d_mean",
        "state_long_run_avg_cf",
        "state_long_run_volatility",
    ]

    feature_rows = []
    for col in feature_candidates:
        corr = actuals.select(
            F.corr(F.col(col), F.col("next_day_daily_region_capacity_factor")).alias("corr")
        ).collect()[0]["corr"]

        feature_rows.append({
            "feature": col,
            "importance": float(abs(corr)) if corr is not None else 0.0,
            "signed_correlation": float(corr) if corr is not None else 0.0,
            "method": "absolute_correlation_with_target",
        })

    feature_rows.sort(key=lambda row: row["importance"], reverse=True)

    with open(website_data_dir / "feature_importance.json", "w") as f:
        json.dump(feature_rows, f, indent=2)

    print("Export complete.")
    print(json.dumps(model_metrics, indent=2))

    spark.stop()


if __name__ == "__main__":
    main()