"""
Train baseline and Random Forest wind forecasting models.

Layer 9 Part A:
- Baseline mean predictor
- Spark ML Random Forest Regressor
- Validation RMSE / MAE
- Reproducible metadata output
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.config import config
from src.common.paths import paths


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_spark(app_name: str = "wind-random-forest-training") -> SparkSession:
    spark_conf = config.spark.get("spark", {})

    builder = SparkSession.builder.appName(
        spark_conf.get("app_name", app_name)
    )

    master = spark_conf.get("master")
    if master:
        builder = builder.master(master)

    for key, value in spark_conf.get("config", {}).items():
        builder = builder.config(key, str(value))

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
        raise ValueError("No numeric feature columns found for model training.")

    return feature_cols


def evaluate_predictions(
    predictions: DataFrame,
    label_col: str,
    prediction_col: str = "prediction",
) -> dict[str, float]:
    rmse_evaluator = RegressionEvaluator(
        labelCol=label_col,
        predictionCol=prediction_col,
        metricName="rmse",
    )

    mae_evaluator = RegressionEvaluator(
        labelCol=label_col,
        predictionCol=prediction_col,
        metricName="mae",
    )

    return {
        "rmse": float(rmse_evaluator.evaluate(predictions)),
        "mae": float(mae_evaluator.evaluate(predictions)),
    }


def train_baseline_mean(
    train_df: DataFrame,
    validation_df: DataFrame,
    target_col: str,
) -> dict[str, Any]:
    mean_value = train_df.select(F.avg(F.col(target_col))).first()[0]

    if mean_value is None or math.isnan(float(mean_value)):
        raise ValueError(f"Could not compute baseline mean for target: {target_col}")

    predictions = validation_df.withColumn("prediction", F.lit(float(mean_value)))

    metrics = evaluate_predictions(
        predictions=predictions,
        label_col=target_col,
    )

    return {
        "model_name": "baseline_mean",
        "model_type": "constant_mean_predictor",
        "prediction_value": float(mean_value),
        "metrics": metrics,
    }


def train_random_forest(
    train_df: DataFrame,
    validation_df: DataFrame,
    target_col: str,
    feature_cols: list[str],
    model_config: dict[str, Any],
) -> tuple[Pipeline, dict[str, Any]]:
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip",
    )

    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol=target_col,
        predictionCol="prediction",
        numTrees=int(model_config.get("num_trees", 50)),
        maxDepth=int(model_config.get("max_depth", 8)),
        seed=int(model_config.get("seed", 42)),
    )

    pipeline = Pipeline(stages=[assembler, rf])
    fitted_model = pipeline.fit(train_df)

    predictions = fitted_model.transform(validation_df)

    metrics = evaluate_predictions(
        predictions=predictions,
        label_col=target_col,
    )

    metadata = {
        "model_name": "random_forest",
        "model_type": "spark_ml_random_forest_regressor",
        "feature_count": len(feature_cols),
        "feature_columns": feature_cols,
        "hyperparameters": {
            "num_trees": int(model_config.get("num_trees", 50)),
            "max_depth": int(model_config.get("max_depth", 8)),
            "seed": int(model_config.get("seed", 42)),
        },
        "metrics": metrics,
    }

    return fitted_model, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/modeling/training_config.yaml",
        help="Path to training config YAML.",
    )
    parser.add_argument(
        "--model-output",
        default=None,
        help="Optional path to save the fitted Random Forest model.",
    )
    parser.add_argument(
        "--metrics-output",
        default="outputs/metrics/random_forest_metrics.json",
        help="Local path for metrics JSON.",
    )
    args = parser.parse_args()

    training_config = load_yaml(args.config)

    spark = create_spark()

    train_path = paths.gold_wind_ml_train
    validation_path = paths.gold_wind_ml_validation

    target_col = training_config["target"]["name"]
    exclude_columns = training_config.get("features", {}).get("exclude_columns", [])

    train_df = spark.read.parquet(train_path)
    validation_df = spark.read.parquet(validation_path)

    train_df = train_df.dropna(subset=[target_col])
    validation_df = validation_df.dropna(subset=[target_col])

    feature_cols = get_feature_columns(
        df=train_df,
        target_col=target_col,
        exclude_columns=exclude_columns,
    )

    baseline_metadata = train_baseline_mean(
        train_df=train_df,
        validation_df=validation_df,
        target_col=target_col,
    )

    fitted_rf_model, rf_metadata = train_random_forest(
        train_df=train_df,
        validation_df=validation_df,
        target_col=target_col,
        feature_cols=feature_cols,
        model_config=training_config["models"]["random_forest"],
    )

    run_metadata = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "training_config": args.config,
        "target": {
            "name": target_col,
            "horizon_days": training_config["target"].get("horizon_days"),
        },
        "datasets": {
            "train_table": train_path,
            "validation_table": validation_path,
        },
        "models": {
            "baseline": baseline_metadata,
            "random_forest": rf_metadata,
        },
    }

    metrics_output = Path(args.metrics_output)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_output, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)

    if args.model_output:
        fitted_rf_model.write().overwrite().save(args.model_output)

    print(json.dumps(run_metadata, indent=2))

    spark.stop()


if __name__ == "__main__":
    main()