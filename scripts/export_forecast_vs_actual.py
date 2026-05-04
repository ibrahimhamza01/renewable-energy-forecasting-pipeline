from pathlib import Path

import pandas as pd
import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.functions import to_date, col


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_spark_from_config(spark_config_path: str, user_config_path: str) -> SparkSession:
    spark_cfg = load_yaml(spark_config_path)["spark"]
    user_cfg = load_yaml(user_config_path)

    master = user_cfg["ec2"].get("spark_master_url") or spark_cfg.get("master", "local[*]")

    builder = (
        SparkSession.builder
        .appName(spark_cfg.get("app_name", "export_forecast_vs_actual"))
        .master(master)
    )

    for key, value in spark_cfg.get("config", {}).items():
        builder = builder.config(key, str(value))

    return builder.getOrCreate()


def s3_path(bucket: str, *parts: str) -> str:
    clean_parts = [str(p).strip("/") for p in parts if p]
    return f"s3a://{bucket}/" + "/".join(clean_parts)


def main():
    user_config_path = "configs/users/syed.yaml"
    spark_config_path = "configs/spark_config.yaml"

    user_cfg = load_yaml(user_config_path)
    bucket = user_cfg["aws"]["project_bucket"]

    forecasts_path = s3_path(
        bucket,
        user_cfg["aws"]["forecasts_prefix"],
        "outputs",
        "run_id=20260504T090915Z",
        "model_version=final_tuned_gbt_20260504T063157Z",
    )

    actuals_path = s3_path(
        bucket,
        user_cfg["aws"]["gold_prefix"],
        "ml",
        "base",
    )

    output_path = Path("website_data/actuals/forecast_vs_actual.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spark = build_spark_from_config(spark_config_path, user_config_path)

    forecasts = spark.read.parquet(forecasts_path)
    actuals = spark.read.parquet(actuals_path)

    forecasts = forecasts.withColumn("date", to_date(col("forecast_date")))
    actuals = actuals.withColumn("date", to_date(col("date_utc")))

    df = forecasts.join(
        actuals,
        on=["date", "state"],
        how="inner",
    )

    df_small = (
        df.select(
            col("date"),
            col("state").alias("region"),
            col("daily_region_capacity_factor").alias("actual"),
            col("prediction").alias("predicted"),
        )
        .filter(col("state") == "TX")
        .limit(300)
    )

    pdf = df_small.toPandas()
    pdf.to_csv(output_path, index=False)

    print(f"Wrote {len(pdf)} rows to {output_path}")


if __name__ == "__main__":
    main()