#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/ubuntu/renewable-energy-forecasting-pipeline"

if [ ! -d "${PROJECT_ROOT}" ]; then
  echo "Project root not found: ${PROJECT_ROOT}"
  exit 1
fi

cd "${PROJECT_ROOT}"

if [ $# -lt 1 ]; then
  echo "Usage:"
  echo "  bash scripts/run_spark_job.sh <python_file> [args...]"
  echo
  echo "Example:"
  echo "  bash scripts/run_spark_job.sh scripts/smoke_test_remote_spark.py"
  exit 1
fi

PYTHON_FILE="$1"
shift

if [ ! -f "${PYTHON_FILE}" ]; then
  echo "Python file not found: ${PYTHON_FILE}"
  exit 1
fi

bash scripts/bootstrap_repo.sh

source .venv/bin/activate
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

SPARK_MASTER_URL="$(python - <<'PY'
from src.common.config import config
print(config.ec2["spark_master_url"])
PY
)"

SPARK_PACKAGES="$(python - <<'PY'
from src.common.config import config
spark_cfg = config.spark["spark"]
print(spark_cfg.get("config", {}).get("spark.jars.packages", ""))
PY
)"

readarray -t SPARK_CONF_LINES < <(python - <<'PY'
from src.common.config import config
spark_cfg = config.spark["spark"]
for key, value in spark_cfg.get("config", {}).items():
    if key == "spark.jars.packages":
        continue
    print(f"{key}={value}")
PY
)

echo "Submitting Spark job..."
echo "Python file: ${PYTHON_FILE}"
echo "Master: ${SPARK_MASTER_URL}"
if [ -n "${SPARK_PACKAGES}" ]; then
  echo "Packages: ${SPARK_PACKAGES}"
fi

CMD=(spark-submit
  --master "${SPARK_MASTER_URL}"
  --deploy-mode client
)

if [ -n "${SPARK_PACKAGES}" ]; then
  CMD+=(--packages "${SPARK_PACKAGES}")
fi

for conf_line in "${SPARK_CONF_LINES[@]}"; do
  CMD+=(--conf "${conf_line}")
done

CMD+=("${PYTHON_FILE}" "$@")

"${CMD[@]}"

echo "Spark job completed."