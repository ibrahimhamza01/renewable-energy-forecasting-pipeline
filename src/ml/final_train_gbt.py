"""
Final tuned GBT training.

Trains on:
- gold/wind/ml/train
- gold/wind/ml/validation

Evaluates once on:
- gold/wind/ml/test

Outputs:
- final Spark ML model artifact
- test metrics JSON
- feature importance JSON
"""

from __future__ import annotations

import argparse
import json
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

from src.common.config import config
from src.common.paths import paths


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_spark(app_name: str = "wind-final-gbt-training") -> SparkSession:
    spark_conf = config.spark.get("spark", {})

    master = config.ec2.get("spark_master_url") or spark_conf.get("master")

    builder = SparkSession.builder.appName(
        spark_conf.get("app_name", app_name)
    )

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


def extract_feature_importance(
    fitted_pipeline_model: Any,
    feature_cols: list[str],
) -> list[dict[str, float]]:
    gbt_model = fitted_pipeline_model.stages[-1]
    importances = gbt_model.featureImportances.toArray().tolist()

    results = [
        {
            "feature": feature,
            "importance": float(importance),
        }
        for feature, importance in zip(feature_cols, importances)
    ]

    return sorted(results, key=lambda x: x["importance"], reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/modeling/training_config.yaml",
    )
    parser.add_argument(
        "--model-output",
        default=None,
        help="S3/local path to save final fitted GBT model.",
    )
    parser.add_argument(
        "--metrics-output",
        default="outputs/metrics/final_gbt_test_metrics.json",
    )
    parser.add_argument(
        "--feature-importance-output",
        default="outputs/metrics/final_gbt_feature_importance.json",
    )
    args = parser.parse_args()

    training_config = load_yaml(args.config)

    spark = create_spark()

    target_col = training_config["target"]["name"]
    exclude_columns = training_config.get("features", {}).get("exclude_columns", [])
    gbt_config = training_config["models"]["gbt"]

    train_df = spark.read.parquet(paths.gold_wind_ml_train).dropna(subset=[target_col])
    validation_df = spark.read.parquet(paths.gold_wind_ml_validation).dropna(subset=[target_col])
    test_df = spark.read.parquet(paths.gold_wind_ml_test).dropna(subset=[target_col])

    final_train_df = train_df.unionByName(validation_df)

    feature_cols = get_feature_columns(
        df=final_train_df,
        target_col=target_col,
        exclude_columns=exclude_columns,
    )

    final_train_df = final_train_df.cache()
    test_df = test_df.cache()

    train_count = final_train_df.count()
    test_count = test_df.count()

    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip",
    )

    gbt = GBTRegressor(
        featuresCol="features",
        labelCol=target_col,
        predictionCol="prediction",
        maxIter=int(gbt_config["max_iter"]),
        maxDepth=int(gbt_config["max_depth"]),
        stepSize=float(gbt_config["step_size"]),
        seed=int(gbt_config.get("seed", 42)),
    )

    pipeline = Pipeline(stages=[assembler, gbt])

    start = time.time()
    model = pipeline.fit(final_train_df)
    training_seconds = time.time() - start

    predictions = model.transform(test_df)
    test_metrics = evaluate_predictions(predictions, target_col)

    feature_importance = extract_feature_importance(model, feature_cols)

    run_metadata = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "training_config": args.config,
        "model_name": "final_tuned_gbt",
        "model_type": "spark_ml_gradient_boosted_trees_regressor",
        "target": {
            "name": target_col,
            "horizon_days": training_config["target"].get("horizon_days"),
        },
        "datasets": {
            "train_table": paths.gold_wind_ml_train,
            "validation_table": paths.gold_wind_ml_validation,
            "test_table": paths.gold_wind_ml_test,
            "final_training_strategy": "train_plus_validation",
        },
        "row_counts": {
            "final_train_rows": train_count,
            "test_rows": test_count,
        },
        "feature_count": len(feature_cols),
        "feature_columns": feature_cols,
        "hyperparameters": {
            "max_iter": int(gbt_config["max_iter"]),
            "max_depth": int(gbt_config["max_depth"]),
            "step_size": float(gbt_config["step_size"]),
            "seed": int(gbt_config.get("seed", 42)),
        },
        "training_seconds": float(training_seconds),
        "test_metrics": test_metrics,
        "top_20_feature_importance": feature_importance[:20],
    }

    metrics_output = Path(args.metrics_output)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_output, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)

    feature_output = Path(args.feature_importance_output)
    feature_output.parent.mkdir(parents=True, exist_ok=True)

    with open(feature_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_timestamp_utc": run_metadata["run_timestamp_utc"],
                "model_name": "final_tuned_gbt",
                "feature_importance": feature_importance,
            },
            f,
            indent=2,
        )

    if args.model_output:
        model.write().overwrite().save(args.model_output)

    print(json.dumps(run_metadata, indent=2))

    spark.stop()


if __name__ == "__main__":
    main()