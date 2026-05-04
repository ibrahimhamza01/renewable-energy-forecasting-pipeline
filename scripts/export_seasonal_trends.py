from pathlib import Path

import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_spark(spark_cfg, user_cfg):
    master = user_cfg["ec2"].get("spark_master_url") or spark_cfg.get("master", "local[*]")

    builder = SparkSession.builder.appName("export_seasonal_trends").master(master)

    for k, v in spark_cfg["config"].items():
        builder = builder.config(k, str(v))

    return builder.getOrCreate()


def s3_path(bucket, *parts):
    return f"s3a://{bucket}/" + "/".join(p.strip("/") for p in parts)


def main():
    user_cfg = load_yaml("configs/users/syed.yaml")
    spark_cfg = load_yaml("configs/spark_config.yaml")["spark"]

    spark = build_spark(spark_cfg, user_cfg)

    df = spark.read.parquet(
        s3_path(
            user_cfg["aws"]["project_bucket"],
            user_cfg["aws"]["gold_prefix"],
            "ml",
            "base",
        )
    )

    df_small = (
        df.select(
            col("season"),
            col("state").alias("region"),
            col("daily_region_capacity_factor").alias("capacity_factor"),
        )
        .filter(col("state").isin("TX", "CA", "FL", "MN"))
    )

    pdf = (
        df_small.toPandas()
        .groupby(["region", "season"])["capacity_factor"]
        .mean()
        .reset_index()
    )

    out = Path("website_data/trends/seasonal_trends.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(out, index=False)

    print(f"Wrote {len(pdf)} rows to {out}")


if __name__ == "__main__":
    main()