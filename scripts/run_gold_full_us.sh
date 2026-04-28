#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_gold_full_us.sh           -> sample mode
#   ./scripts/run_gold_full_us.sh sample    -> sample mode
#   ./scripts/run_gold_full_us.sh full      -> full all-years
#   ./scripts/run_gold_full_us.sh full 2025 -> full single year

MODE="${1:-sample}"
YEAR="${2:-}"

if [[ "$MODE" != "sample" && "$MODE" != "full" ]]; then
  echo "MODE must be sample or full"
  exit 1
fi

export PROJECT_USER_CONFIG="${PROJECT_USER_CONFIG:-configs/users/syed.yaml}"
export PYTHONPATH="${PYTHONPATH:-$PWD}"

SPARK_MASTER="${SPARK_MASTER:-spark://ip-172-31-83-109.ec2.internal:7077}"

echo "Running Layer 6 Part B Gold build"
echo "MODE=$MODE"
echo "YEAR=${YEAR:-ALL}"
echo "PROJECT_USER_CONFIG=$PROJECT_USER_CONFIG"
echo "SPARK_MASTER=$SPARK_MASTER"

CMD=(
  spark-submit
  --master "$SPARK_MASTER"
  --deploy-mode client
  --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
  --conf spark.hadoop.fs.s3a.aws.credentials.provider=com.amazonaws.auth.DefaultAWSCredentialsProviderChain
  scripts/build_gold_wind_tables.py
  --mode "$MODE"
)

if [[ -n "$YEAR" ]]; then
  CMD+=(--year "$YEAR")
fi

"${CMD[@]}"