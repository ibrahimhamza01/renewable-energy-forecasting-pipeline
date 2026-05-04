from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.config import config
from src.common.spark_utils import get_spark_session
from src.ml.inference import run_batch_inference


def _s3_base() -> str:
    bucket = (
        config.aws.get("project_bucket")
        or config.aws.get("s3_bucket")
        or config.aws.get("bucket")
    )

    if not bucket:
        raise KeyError(
            "No S3 bucket found in user config. Expected one of: "
            "aws.project_bucket, aws.s3_bucket, or aws.bucket"
        )

    return f"s3a://{bucket}"


def resolve_path(*keys: str) -> str:
    node: Any = config.paths

    for key in keys:
        node = node[key]

    return f"{_s3_base()}/{node.strip('/')}"


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def get_forecast_output_path(run_id: str) -> str:
    base_path = resolve_path("forecasts", "outputs")
    return f"{base_path}/run_id={run_id}"


def validate_forecast_output(df: DataFrame) -> None:
    required_columns = [
        "forecast_id",
        "forecast_date",
        "state",
        "target_name",
        "prediction",
        "model_name",
        "model_version",
        "generation_timestamp",
        "horizon_days",
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Forecast output missing required columns: {missing}")

    null_checks = (
        df.select(
            *[
                F.count(F.when(F.col(col).isNull(), col)).alias(col)
                for col in required_columns
            ]
        )
        .collect()[0]
        .asDict()
    )

    bad_nulls = {k: v for k, v in null_checks.items() if v > 0}

    if bad_nulls:
        raise ValueError(f"Forecast output has nulls in required columns: {bad_nulls}")


def summarize_forecasts(df: DataFrame) -> dict:
    row = (
        df.agg(
            F.count("*").alias("row_count"),
            F.countDistinct("state").alias("state_count"),
            F.min("forecast_date").alias("min_forecast_date"),
            F.max("forecast_date").alias("max_forecast_date"),
            F.min("prediction").alias("min_prediction"),
            F.max("prediction").alias("max_prediction"),
            F.avg("prediction").alias("avg_prediction"),
            F.countDistinct("model_version").alias("model_version_count"),
        )
        .collect()[0]
        .asDict()
    )

    return {k: str(v) if v is not None else None for k, v in row.items()}


def write_forecast_outputs(df: DataFrame, run_id: str | None = None) -> str:
    if run_id is None:
        run_id = make_run_id()

    output_path = get_forecast_output_path(run_id)

    validate_forecast_output(df)
    df = df.repartition(50)

    (
        df.write.mode("overwrite")
        .partitionBy("model_version")
        .parquet(output_path)
    )

    return output_path


def write_forecast_metadata(
    spark: SparkSession,
    forecast_df: DataFrame,
    output_path: str,
    run_id: str,
) -> str:
    metadata = {
        "run_id": run_id,
        "output_path": output_path,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_name": forecast_df.select("target_name").first()["target_name"],
        "model_name": forecast_df.select("model_name").first()["model_name"],
        "model_version": forecast_df.select("model_version").first()["model_version"],
        "summary": summarize_forecasts(forecast_df),
    }

    metadata_path = f"{output_path}_metadata"

    metadata_df = spark.createDataFrame(
        [(json.dumps(metadata, indent=2),)],
        ["metadata_json"],
    )

    metadata_df.coalesce(1).write.mode("overwrite").text(metadata_path)

    return metadata_path


def export_batch_forecasts() -> tuple[str, str]:
    spark = get_spark_session()

    run_id = make_run_id()

    forecast_df = run_batch_inference()

    output_path = write_forecast_outputs(forecast_df, run_id=run_id)

    metadata_path = write_forecast_metadata(
        spark=spark,
        forecast_df=forecast_df,
        output_path=output_path,
        run_id=run_id,
    )

    return output_path, metadata_path


if __name__ == "__main__":
    output_path, metadata_path = export_batch_forecasts()

    print(f"Forecast outputs written to: {output_path}")
    print(f"Forecast metadata written to: {metadata_path}")