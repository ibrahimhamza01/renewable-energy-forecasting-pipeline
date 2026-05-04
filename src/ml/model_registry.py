"""
Register trained wind forecasting models in S3.

Layer 9 Part B:
- Creates timestamped model version metadata
- Records training/test metrics
- Records feature list and hyperparameters
- Writes latest model pointer
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.aws_utils import s3a_to_s3_uri, upload_json_to_s3
from src.common.paths import paths


def load_local_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_model_version_id(model_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{model_name}_{timestamp}"


def build_registry_metadata(
    metrics: dict[str, Any],
    model_artifact_path: str,
    model_version_id: str,
    status: str,
) -> dict[str, Any]:
    return {
        "model_version_id": model_version_id,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "model_name": metrics["model_name"],
        "model_type": metrics["model_type"],
        "target": metrics["target"],
        "model_artifact_path_spark": model_artifact_path,
        "model_artifact_path_s3": s3a_to_s3_uri(model_artifact_path),
        "training_config": metrics["training_config"],
        "datasets": metrics["datasets"],
        "row_counts": metrics["row_counts"],
        "feature_count": metrics["feature_count"],
        "feature_columns": metrics["feature_columns"],
        "hyperparameters": metrics["hyperparameters"],
        "training_seconds": metrics["training_seconds"],
        "test_metrics": metrics["test_metrics"],
        "top_20_feature_importance": metrics["top_20_feature_importance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics-json",
        default="outputs/metrics/final_gbt_test_metrics.json",
    )
    parser.add_argument(
        "--model-artifact-path",
        default=None,
    )
    parser.add_argument(
        "--status",
        default="production_candidate",
        choices=["candidate", "production_candidate", "production"],
    )
    args = parser.parse_args()

    metrics = load_local_json(args.metrics_json)

    model_version_id = build_model_version_id(metrics["model_name"])

    model_artifact_path = args.model_artifact_path or f"{paths.model_registry}/final_gbt"

    metadata = build_registry_metadata(
        metrics=metrics,
        model_artifact_path=model_artifact_path,
        model_version_id=model_version_id,
        status=args.status,
    )

    registry_base = paths.model_registry

    version_metadata_uri = (
        f"{registry_base}/versions/{model_version_id}/model_version.json"
    )

    latest_metadata_uri = f"{registry_base}/latest/model_version.json"

    upload_json_to_s3(metadata, version_metadata_uri)
    upload_json_to_s3(metadata, latest_metadata_uri)

    print(json.dumps(
        {
            "registered": True,
            "model_version_id": model_version_id,
            "status": args.status,
            "version_metadata_uri": version_metadata_uri,
            "latest_metadata_uri": latest_metadata_uri,
            "model_artifact_path": model_artifact_path,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()