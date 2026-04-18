#!/usr/bin/env bash

set -euo pipefail

APP_NAME="local-sample-parse-pipeline"

echo "Starting local sample parsing pipeline..."

python -m src.parsing.run_local_sample_pipeline

echo "Local sample parsing pipeline completed."