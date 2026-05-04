#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_USER_CONFIG:?PROJECT_USER_CONFIG is not set}"

MODEL_OUTPUT=$(python - <<'PY'
from src.common.paths import paths
print(paths.model_registry + "/gbt_test")
PY
)

python -m src.ml.train_gbt \
  --config configs/modeling/training_config.yaml \
  --metrics-output outputs/metrics/gbt_metrics.json \
  --model-output "${MODEL_OUTPUT}"