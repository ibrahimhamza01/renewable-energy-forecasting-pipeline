"""
Tune Spark ML GBTRegressor using a time-series-safe validation split.

This does NOT use random k-fold CV.
It trains on gold/wind/ml/train and evaluates on gold/wind/ml/validation.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.config import config
from src.common.paths import paths


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_spark(app_name: str = "wind-gbt-hyperparameter-tuning") -> SparkSession:
    spark_conf = config.spark.get("spark", {})

    builder = SparkSession.builder.appName(
        spark_conf.get("app_name", app_name)
    )

    master = config.ec2.get("spark_master_url") or spark_conf.get("master")
    if master:
        builder = builder.master(master)

    for key, value in spark_conf.get("config", {}).items():
        builder = builder.config(key, str(value))

    print(f"Using Spark master: {master}")

    return builder.getOrCreate()


def get_feature_columns(
    df: DataFrame,
    target_col: str,
    exclude_columns: list[str],
) -> list[str]:
    excluded = set(exclude_columns)
    excluded.add(target_col)

    numeric_types = {
        "int",
        "bigint",
        "double",
        "float",
        "decimal",
        "long",
        "short",
    }

    feature_cols: list[str] = []

    for field in df.schema.fields:
        col_name = field.name
        dtype = field.dataType.simpleString().lower()

        if col_name in excluded:
            continue

        if any(dtype.startswith(t) for t in numeric_types):
            feature_cols.append(col_name)

    if not feature_cols:
        raise ValueError("No numeric feature columns found.")

    return feature_cols


def evaluate_predictions(
    predictions: DataFrame,
    label_col: str,
) -> dict[str, float]:
    rmse = RegressionEvaluator(
        labelCol=label_col,
        predictionCol="prediction",
        metricName="rmse",
    ).evaluate(predictions)

    mae = RegressionEvaluator(
        labelCol=label_col,
        predictionCol="prediction",
        metricName="mae",
    ).evaluate(predictions)

    return {
        "rmse": float(rmse),
        "mae": float(mae),
    }


def baseline_mean(
    train_df: DataFrame,
    validation_df: DataFrame,
    target_col: str,
) -> dict[str, Any]:
    mean_value = train_df.select(F.avg(F.col(target_col))).first()[0]

    if mean_value is None or math.isnan(float(mean_value)):
        raise ValueError(f"Could not compute baseline mean for {target_col}")

    predictions = validation_df.withColumn("prediction", F.lit(float(mean_value)))

    return {
        "model_name": "baseline_mean",
        "prediction_value": float(mean_value),
        "metrics": evaluate_predictions(predictions, target_col),
    }


def train_one_gbt(
    train_df: DataFrame,
    validation_df: DataFrame,
    target_col: str,
    feature_cols: list[str],
    params: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip",
    )

    gbt = GBTRegressor(
        featuresCol="features",
        labelCol=target_col,
        predictionCol="prediction",
        maxIter=int(params["max_iter"]),
        maxDepth=int(params["max_depth"]),
        stepSize=float(params["step_size"]),
        seed=int(params.get("seed", 42)),
    )

    pipeline = Pipeline(stages=[assembler, gbt])

    start = time.time()
    model = pipeline.fit(train_df)
    train_seconds = time.time() - start

    predictions = model.transform(validation_df)
    metrics = evaluate_predictions(predictions, target_col)

    result = {
        "params": {
            "max_iter": int(params["max_iter"]),
            "max_depth": int(params["max_depth"]),
            "step_size": float(params["step_size"]),
            "seed": int(params.get("seed", 42)),
        },
        "metrics": metrics,
        "training_seconds": float(train_seconds),
    }

    return model, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/modeling/training_config.yaml",
    )
    parser.add_argument(
        "--metrics-output",
        default="outputs/metrics/gbt_tuning_metrics.json",
    )
    parser.add_argument(
        "--best-model-output",
        default=None,
        help="Optional S3/local path to save the best validation GBT model.",
    )
    args = parser.parse_args()

    training_config = load_yaml(args.config)

    spark = create_spark()

    target_col = training_config["target"]["name"]
    exclude_columns = training_config.get("features", {}).get("exclude_columns", [])

    train_df = spark.read.parquet(paths.gold_wind_ml_train).dropna(subset=[target_col])
    validation_df = spark.read.parquet(paths.gold_wind_ml_validation).dropna(subset=[target_col])

    feature_cols = get_feature_columns(
        df=train_df,
        target_col=target_col,
        exclude_columns=exclude_columns,
    )

    train_df = train_df.cache()
    validation_df = validation_df.cache()

    _ = train_df.count()
    _ = validation_df.count()

    tuning_grid = training_config["tuning"]["gbt"]
    base_gbt_config = training_config["models"]["gbt"]

    param_grid = list(
        itertools.product(
            tuning_grid["max_iter"],
            tuning_grid["max_depth"],
            tuning_grid["step_size"],
        )
    )

    baseline = baseline_mean(
        train_df=train_df,
        validation_df=validation_df,
        target_col=target_col,
    )

    all_results: list[dict[str, Any]] = []
    best_model = None
    best_result = None

    for max_iter, max_depth, step_size in param_grid:
        params = {
            "max_iter": max_iter,
            "max_depth": max_depth,
            "step_size": step_size,
            "seed": base_gbt_config.get("seed", 42),
        }

        model, result = train_one_gbt(
            train_df=train_df,
            validation_df=validation_df,
            target_col=target_col,
            feature_cols=feature_cols,
            params=params,
        )

        all_results.append(result)

        if best_result is None or result["metrics"]["rmse"] < best_result["metrics"]["rmse"]:
            best_result = result
            best_model = model

        print(json.dumps(result, indent=2))

    assert best_model is not None
    assert best_result is not None

    run_metadata = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "training_config": args.config,
        "target": {
            "name": target_col,
            "horizon_days": training_config["target"].get("horizon_days"),
        },
        "datasets": {
            "train_table": paths.gold_wind_ml_train,
            "validation_table": paths.gold_wind_ml_validation,
        },
        "feature_count": len(feature_cols),
        "feature_columns": feature_cols,
        "baseline": baseline,
        "model": "gbt",
        "selection_metric": "validation_rmse",
        "candidate_count": len(all_results),
        "best_result": best_result,
        "all_results": sorted(
            all_results,
            key=lambda x: x["metrics"]["rmse"],
        ),
    }

    metrics_output = Path(args.metrics_output)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_output, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)

    if args.best_model_output:
        best_model.write().overwrite().save(args.best_model_output)

    print("\nBEST GBT CONFIG")
    print(json.dumps(best_result, indent=2))
    print(f"\nSaved metrics to: {metrics_output}")

    spark.stop()


if __name__ == "__main__":
    main()