from pathlib import Path

import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def s3_path(bucket, *parts):
    return f"s3a://{bucket}/" + "/".join(str(p).strip("/") for p in parts if p)


def build_spark():
    spark_cfg = load_yaml("configs/spark_config.yaml")["spark"]
    user_cfg = load_yaml("configs/users/syed.yaml")

    builder = (
        SparkSession.builder
        .appName("export_wind_map_data")
        .master(user_cfg["ec2"].get("spark_master_url", "local[*]"))
    )

    for k, v in spark_cfg["config"].items():
        builder = builder.config(k, str(v))

    return builder.getOrCreate(), user_cfg


def main():
    spark, user_cfg = build_spark()
    bucket = user_cfg["aws"]["project_bucket"]

    silver_path = s3_path(
        bucket,
        user_cfg["aws"]["silver_prefix"],
        "year=2025",
    )

    df = spark.read.option("mergeSchema", "false").parquet(silver_path)

    map_df = (
        df.select(
            col("station_id"),
            col("LATITUDE").cast("double").alias("latitude"),
            col("LONGITUDE").cast("double").alias("longitude"),
            col("state"),
            col("wind_speed_ms"),
        )
        .where(col("latitude").isNotNull())
        .where(col("longitude").isNotNull())
        .where(col("wind_speed_ms").isNotNull())
        .groupBy("station_id", "latitude", "longitude", "state")
        .agg(avg("wind_speed_ms").alias("avg_wind_speed_ms"))
    )

    out = Path("website_data/maps/us_wind_station_map.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    pdf = map_df.toPandas()
    pdf.to_csv(out, index=False)

    print(f"Wrote {len(pdf)} rows to {out}")


if __name__ == "__main__":
    main()