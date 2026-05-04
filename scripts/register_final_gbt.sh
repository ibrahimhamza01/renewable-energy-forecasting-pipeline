#!/usr/bin/env bash
set -euo pipefail

export PROJECT_USER_CONFIG=configs/users/syed.yaml

MODEL_ARTIFACT_PATH=$(python - <<'PY'
from src.common.paths import paths
print(paths.model_registry + "/final_gbt")
PY
)

python -m src.ml.model_registry \
  --metrics-json outputs/metrics/final_gbt_test_metrics.json \
  --model-artifact-path "$MODEL_ARTIFACT_PATH" \
  --status production_candidate