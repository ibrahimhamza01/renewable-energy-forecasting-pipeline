from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml
from pyspark.ml import PipelineModel
from pyspark.ml.regression import GBTRegressionModel
from pyspark.sql import SparkSession


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def deep_get(d: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def build_spark(spark_config: dict[str, Any], user_config: dict[str, Any]) -> SparkSession:
    spark_section = spark_config.get("spark", {})

    builder = (
        SparkSession.builder
        .appName("export-model-registry-metadata")
        .master(
            deep_get(
                user_config,
                ["ec2", "spark_master_url"],
                spark_section.get("master", "local[*]"),
            )
        )
    )

    for key, value in spark_section.get("config", {}).items():
        builder = builder.config(key, str(value))

    return builder.getOrCreate()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    user_cfg = load_yaml(
        repo_root / os.environ.get(
            "PROJECT_USER_CONFIG",
            "configs/users/syed.yaml"
        )
    )

    bucket = deep_get(user_cfg, ["aws", "project_bucket"])

    model_path = (
        f"s3a://{bucket}/models/registry/final_gbt"
    )

    out_dir = repo_root / "website" / "public" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    spark_config = load_yaml(repo_root / "configs/spark_config.yaml")
    spark = build_spark(spark_config, user_cfg)

    print(f"Loading pipeline model from: {model_path}")

    pipeline = PipelineModel.load(model_path)

    stages = pipeline.stages

    pipeline_summary = {
        "model_registry_path": model_path,
        "total_stages": len(stages),
        "stages": [],
    }

    gbt_stage = None

    for idx, stage in enumerate(stages):
        stage_info = {
            "index": idx,
            "class": stage.__class__.__name__,
            "uid": stage.uid,
        }

        pipeline_summary["stages"].append(stage_info)

        if isinstance(stage, GBTRegressionModel):
            gbt_stage = stage

    with open(out_dir / "model_pipeline_summary.json", "w") as f:
        json.dump(pipeline_summary, f, indent=2)

    if gbt_stage is not None:
        print("Extracting GBT metadata...")

        importances = gbt_stage.featureImportances

        feature_importance = []
        for i, val in enumerate(importances):
            feature_importance.append({
                "feature_index": i,
                "importance": float(val),
            })

        feature_importance.sort(
            key=lambda x: x["importance"],
            reverse=True
        )

        with open(out_dir / "true_feature_importance.json", "w") as f:
            json.dump(feature_importance, f, indent=2)

        hyperparams = {
            "maxDepth": gbt_stage.getMaxDepth(),
            "maxBins": gbt_stage.getMaxBins(),
            "maxIter": gbt_stage.getMaxIter(),
            "stepSize": gbt_stage.getStepSize(),
            "subsamplingRate": gbt_stage.getSubsamplingRate(),
            "lossType": gbt_stage.getLossType(),
            "treeWeights": [float(x) for x in gbt_stage.treeWeights],
            "numTrees": len(gbt_stage.trees),
        }

        with open(out_dir / "model_hyperparameters.json", "w") as f:
            json.dump(hyperparams, f, indent=2)

        print(json.dumps(hyperparams, indent=2))

    else:
        print("No GBTRegressionModel found in pipeline.")

    spark.stop()


if __name__ == "__main__":
    main()