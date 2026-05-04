"""
Layer 7 Part B: Build Gold extreme event windows table.

Reads:
    s3a://<project_bucket>/<gold_prefix>/analytics/daily_region

Writes:
    s3a://<project_bucket>/<gold_prefix>/analytics/extreme_events

This script is config-driven and does not hardcode S3 buckets or prefixes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from pyspark.sql import functions as F

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------


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
        raise ValueError(
            "PROJECT_USER_CONFIG environment variable must be set. "
            "Example: export PROJECT_USER_CONFIG=configs/users/syed.yaml"
        )

    config_path = project_root / config_env

    if not config_path.exists():
        raise FileNotFoundError(f"User config not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------
# Main job
# ---------------------------------------------------------------------


def main() -> None:
    project_root = find_project_root()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    from src.common.spark_utils import get_spark_session
    from src.storage.table_builders import build_gold_extreme_event_windows
    from src.storage.write_gold import write_gold_table

    user_config = load_user_config(project_root)

    bucket = user_config["aws"]["project_bucket"]
    gold_prefix = user_config["aws"]["gold_prefix"]

    gold_root = f"s3a://{bucket}/{gold_prefix}"

    input_path = f"{gold_root}/analytics/daily_region"
    output_path = f"{gold_root}/analytics/extreme_events"

    print("Project root:", project_root)
    print("Input path:", input_path)
    print("Output path:", output_path)

    spark = get_spark_session(app_name="layer7_build_gold_extreme_events")
    spark.sparkContext.setLogLevel("WARN")

    # Read already-built Layer 7 daily analytical table
    daily_region = spark.read.parquet(input_path)

    # Build extreme event table
    extreme_events = build_gold_extreme_event_windows(daily_region)

    # Basic pre-write validation
    validation = extreme_events.select(
        F.count("*").alias("rows"),
        F.countDistinct("state", "date_utc").alias("distinct_grain"),
        F.min("daily_region_capacity_factor").alias("min_daily_cf"),
        F.max("daily_region_capacity_factor").alias("max_daily_cf"),
        F.min("capacity_factor_z_score").alias("min_z"),
        F.max("capacity_factor_z_score").alias("max_z"),
    )

    print("Pre-write validation:")
    validation.show(truncate=False)

    print("Extreme event type counts:")
    extreme_events.groupBy("extreme_event_type").count().show(truncate=False)

    # Write output
    #
    # Coalesce avoids excessive small files for this medium-sized analytical table.
    write_gold_table(
        extreme_events.coalesce(8),
        output_path=output_path,
        partition_cols=["year", "state"],
        mode="overwrite",
    )

    print(f"Wrote gold_extreme_event_windows to: {output_path}")

    # Read-back validation
    readback = spark.read.parquet(output_path)

    print("Read-back validation:")
    readback.select(
        F.count("*").alias("rows"),
        F.countDistinct("state", "date_utc").alias("distinct_grain"),
    ).show(truncate=False)

    print("Read-back extreme event type counts:")
    readback.groupBy("extreme_event_type").count().show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()