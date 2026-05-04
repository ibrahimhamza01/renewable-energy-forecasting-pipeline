#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_USER_CONFIG:?PROJECT_USER_CONFIG is not set}"

BEST_MODEL_OUTPUT=$(python - <<'PY'
from src.common.paths import paths
print(paths.model_registry + "/gbt_tuned_validation_best")
PY
)

python -m src.ml.tune_gbt \
  --config configs/modeling/training_config.yaml \
  --metrics-output outputs/metrics/gbt_tuning_metrics.json \
  --best-model-output "${BEST_MODEL_OUTPUT}"