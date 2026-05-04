import yaml
from pyspark.sql import SparkSession


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
        .appName("inspect_geo_tables")
        .master(user_cfg["ec2"].get("spark_master_url", "local[*]"))
    )

    for k, v in spark_cfg["config"].items():
        builder = builder.config(k, str(v))

    return builder.getOrCreate(), user_cfg


def inspect(spark, path):
    print("\n" + "=" * 80)
    print(path)
    try:
        df = spark.read.parquet(path)
        print(df.columns)
        df.printSchema()
    except Exception as e:
        print("FAILED:", e)


def main():
    spark, user_cfg = build_spark()
    bucket = user_cfg["aws"]["project_bucket"]

    candidates = [
        s3_path(bucket, user_cfg["aws"]["silver_prefix"]),
        s3_path(bucket, user_cfg["aws"]["gold_prefix"], "analytics", "daily_region"),
        s3_path(bucket, user_cfg["aws"]["gold_prefix"], "analytics", "monthly_state"),
        s3_path(bucket, user_cfg["aws"]["gold_prefix"], "ml", "base"),
    ]

    for path in candidates:
        inspect(spark, path)


if __name__ == "__main__":
    main()