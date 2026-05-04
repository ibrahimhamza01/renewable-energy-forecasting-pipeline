from pathlib import Path

import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_spark_from_config(spark_config_path: str, user_config_path: str) -> SparkSession:
    spark_cfg = load_yaml(spark_config_path)["spark"]
    user_cfg = load_yaml(user_config_path)

    master = user_cfg["ec2"].get("spark_master_url") or spark_cfg.get("master", "local[*]")

    builder = (
        SparkSession.builder
        .appName("export_regional_trends")
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

    actuals_path = s3_path(
        bucket,
        user_cfg["aws"]["gold_prefix"],
        "ml",
        "base",
    )

    output_path = Path("website_data/trends/regional_trends.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spark = build_spark_from_config(spark_config_path, user_config_path)

    df = spark.read.parquet(actuals_path)

    df_small = (
        df.withColumn("date", to_date(col("date_utc")))
        .select(
            col("date"),
            col("state").alias("region"),
            col("daily_region_capacity_factor").alias("capacity_factor"),
        )
        .filter(col("state").isin("TX", "CA", "FL", "MN"))
        .orderBy("date", "state")
        .limit(3000)
    )

    pdf = df_small.toPandas()
    pdf.to_csv(output_path, index=False)

    print(f"Wrote {len(pdf)} rows to {output_path}")


if __name__ == "__main__":
    main()