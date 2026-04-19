#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/ubuntu/renewable-energy-forecasting-pipeline"

if [ ! -d "${PROJECT_ROOT}" ]; then
  echo "Project root not found: ${PROJECT_ROOT}"
  exit 1
fi

cd "${PROJECT_ROOT}"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed or not on PATH"
  exit 1
fi

echo "Syncing project environment..."
uv sync

source .venv/bin/activate

if [ -f ".env" ]; then
  echo "Loading .env file..."
  set -a
  source .env
  set +a
fi

: "${PROJECT_USER_CONFIG:?PROJECT_USER_CONFIG is not set}"

python - <<'PY'
from src.common.config import config
from src.common.paths import paths

print("Config loaded successfully")
print(f"User: {config.user['name']}")
print(f"AWS region: {config.aws['region']}")
print(f"Spark master URL: {config.ec2['spark_master_url']}")
print(f"Raw ISD path: {paths.raw_isd}")
print(f"Bronze ISD path: {paths.bronze_isd}")
print(f"Silver weather path: {paths.silver_weather}")
print(f"Output figures path: {paths.output_figures}")
PY

echo "Repository bootstrap complete."