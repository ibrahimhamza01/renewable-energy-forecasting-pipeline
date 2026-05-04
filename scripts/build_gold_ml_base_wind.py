"""
Layer 7 Part B: Build Gold ML base wind table.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from pyspark.sql import functions as F


def find_project_root() -> Path:
    project_root = Path.cwd()
    while not (project_root / "configs").exists():
        if project_root.parent == project_root:
            raise RuntimeError("Could not find project root containing configs/")
        project_root = project_root.parent
    return project_root


def load_user_config(project_root: Path) -> dict:
    config_env = os.environ.get("PROJECT_USER_CONFIG")
    if config_env is None:
        raise ValueError("PROJECT_USER_CONFIG must be set")

    config_path = project_root / config_env
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    project_root = find_project_root()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    from src.common.spark_utils import get_spark_session
    from src.storage.table_builders import build_gold_ml_base_wind
    from src.storage.write_gold import write_gold_table

    user_config = load_user_config(project_root)

    bucket = user_config["aws"]["project_bucket"]
    gold_prefix = user_config["aws"]["gold_prefix"]
    gold_root = f"s3a://{bucket}/{gold_prefix}"

    input_path = f"{gold_root}/analytics/daily_region"
    output_path = f"{gold_root}/ml/base"

    print("Input path:", input_path)
    print("Output path:", output_path)

    spark = get_spark_session(
        app_name="layer7_build_gold_ml_base_wind",
        master="local[*]",
    )
    spark.sparkContext.setLogLevel("WARN")

    daily_region = spark.read.parquet(input_path)

    ml_base = build_gold_ml_base_wind(daily_region)

    print("Pre-write validation:")
    ml_base.select(
        F.count("*").alias("rows"),
        F.countDistinct("state", "date_utc").alias("distinct_grain"),
        F.min("next_day_daily_region_capacity_factor").alias("min_target"),
        F.max("next_day_daily_region_capacity_factor").alias("max_target"),
    ).show(truncate=False)

    print("Null target check:")
    ml_base.where(
        F.col("next_day_daily_region_capacity_factor").isNull()
    ).count()

    write_gold_table(
        ml_base.coalesce(8),
        output_path=output_path,
        partition_cols=["year", "state"],
        mode="overwrite",
    )

    print(f"Wrote gold_ml_base_wind to: {output_path}")

    readback = spark.read.parquet(output_path)

    print("Read-back validation:")
    readback.select(
        F.count("*").alias("rows"),
        F.countDistinct("state", "date_utc").alias("distinct_grain"),
        F.min("next_day_daily_region_capacity_factor").alias("min_target"),
        F.max("next_day_daily_region_capacity_factor").alias("max_target"),
    ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()