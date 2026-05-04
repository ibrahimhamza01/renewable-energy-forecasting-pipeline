from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyspark.ml import PipelineModel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from src.common.config import config
from src.common.spark_utils import get_spark_session


MODEL_NAME = "final_tuned_gbt"
TARGET_NAME = "next_day_daily_region_capacity_factor"
HORIZON_DAYS = 1


def _s3_base() -> str:
    bucket = config.aws["project_bucket"]
    return f"s3a://{bucket}"


def resolve_path(*keys: str) -> str:
    """
    Resolve logical paths from configs/paths.yaml into full S3 paths.

    Example:
        resolve_path("gold", "wind_ml_features")
        -> s3a://bucket/gold/wind/ml/features
    """
    node: Any = config.paths
    for key in keys:
        node = node[key]

    return f"{_s3_base()}/{node.strip('/')}"


def load_latest_features(spark: SparkSession) -> DataFrame:
    feature_path = resolve_path("gold", "wind_ml_features")
    return spark.read.parquet(feature_path)


def _read_registry_metadata(spark: SparkSession) -> dict:
    registry_path = resolve_path("models", "registry")
    metadata_path = f"{registry_path}/latest/model_version.json"

    rows = spark.read.text(metadata_path).collect()
    metadata = json.loads("\n".join(row["value"] for row in rows))

    if "model_path" not in metadata:
        metadata["model_path"] = f"{registry_path}/final_gbt"

    if "model_name" not in metadata:
        metadata["model_name"] = MODEL_NAME

    if "model_version" not in metadata:
        metadata["model_version"] = metadata.get(
            "version_id",
            "final_tuned_gbt_20260504T063157Z"
        )

    return metadata


def load_production_model(spark: SparkSession):
    """
    Load the approved production candidate model.

    Expected metadata fields:
        model_name
        model_version
        model_path

    model_path should be a full s3a:// path to the Spark ML model artifact.
    """
    metadata = _read_registry_metadata(spark)

    model_path = metadata["model_path"]
    model = PipelineModel.load(model_path)

    return model, metadata


def generate_predictions(model: PipelineModel, features_df: DataFrame) -> DataFrame:
    return model.transform(features_df)


def standardize_forecast_output(
    df: DataFrame,
    model_metadata: dict,
    horizon_days: int = HORIZON_DAYS,
) -> DataFrame:
    uuid_udf = F.udf(lambda: str(uuid.uuid4()), StringType())

    model_name = model_metadata.get("model_name", MODEL_NAME)
    model_version = model_metadata.get("model_version", "unknown_model_version")

    forecast_df = (
        df.withColumn("forecast_id", uuid_udf())
        .withColumn("forecast_date", F.col("date_utc").cast("date"))
        .withColumn("target_name", F.lit(TARGET_NAME))
        .withColumn("model_name", F.lit(model_name))
        .withColumn("model_version", F.lit(model_version))
        .withColumn("generation_timestamp", F.current_timestamp())
        .withColumn("horizon_days", F.lit(horizon_days))
    )

    if "region" not in forecast_df.columns:
        forecast_df = forecast_df.withColumn("region", F.lit(None).cast("string"))

    return forecast_df.select(
        "forecast_id",
        "forecast_date",
        "region",
        "state",
        "target_name",
        F.col("prediction").cast("double").alias("prediction"),
        "model_name",
        "model_version",
        "generation_timestamp",
        "horizon_days",
    )


def run_batch_inference() -> DataFrame:
    spark = get_spark_session()

    features_df = load_latest_features(spark)
    model, metadata = load_production_model(spark)

    predictions_df = generate_predictions(model, features_df)

    forecast_df = standardize_forecast_output(
        predictions_df,
        model_metadata=metadata,
        horizon_days=HORIZON_DAYS,
    )

    return forecast_df


if __name__ == "__main__":
    df = run_batch_inference()
    df.printSchema()
    df.show(20, truncate=False)