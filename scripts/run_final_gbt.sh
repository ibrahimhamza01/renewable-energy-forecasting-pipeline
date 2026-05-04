#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " FINAL GBT TRAINING (TRAIN+VAL → TEST)"
echo "=========================================="

# --- ENV ---
export PROJECT_USER_CONFIG=configs/users/syed.yaml
export SPARK_HOME=/opt/spark
export PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH

# --- OUTPUT PATHS ---
MODEL_OUTPUT=$(python - <<'PY'
from src.common.paths import paths
print(paths.model_registry + "/final_gbt")
PY
)
METRICS_OUTPUT="outputs/metrics/final_gbt_test_metrics.json"
FEATURE_OUTPUT="outputs/metrics/final_gbt_feature_importance.json"

echo "Model output: $MODEL_OUTPUT"
echo "Metrics output: $METRICS_OUTPUT"
echo "Feature importance output: $FEATURE_OUTPUT"

echo "------------------------------------------"
echo "Running final GBT training..."
echo "------------------------------------------"

python -m src.ml.final_train_gbt \
  --model-output "$MODEL_OUTPUT" \
  --metrics-output "$METRICS_OUTPUT" \
  --feature-importance-output "$FEATURE_OUTPUT"

echo "------------------------------------------"
echo "FINAL GBT TRAINING COMPLETE"
echo "------------------------------------------"