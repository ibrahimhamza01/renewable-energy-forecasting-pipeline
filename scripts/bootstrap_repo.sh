#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found. Run: uv sync"
  exit 1
fi

source .venv/bin/activate

if [ -f ".env" ]; then
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
print(f"Raw ISD path: {paths.raw_isd}")
print(f"Silver weather path: {paths.silver_weather}")
print(f"Output figures path: {paths.output_figures}")
PY
