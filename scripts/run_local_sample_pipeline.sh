#!/usr/bin/env bash

set -euo pipefail

APP_NAME="local-sample-cleaned-pipeline"

echo "Starting local sample cleaned pipeline..."

export PROJECT_USER_CONFIG="configs/users/syed.yaml"

python -m src.cleaning.run_local_sample_pipeline

echo "Local sample cleaned pipeline completed."