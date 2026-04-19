#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/ubuntu/renewable-energy-forecasting-pipeline"
SPARK_VERSION="3.5.6"
HADOOP_VERSION="3"
SPARK_DIR="/opt/spark"
SPARK_ARCHIVE="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}"
SPARK_TGZ="${SPARK_ARCHIVE}.tgz"
SPARK_URL="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_TGZ}"

echo "Running shared dependency installation..."
bash "${PROJECT_ROOT}/infra/aws/bootstrap/install_dependencies.sh"

echo "Checking project root..."
if [ ! -d "${PROJECT_ROOT}" ]; then
  echo "Project root not found: ${PROJECT_ROOT}"
  exit 1
fi

cd "${PROJECT_ROOT}"

if [ -z "${PROJECT_USER_CONFIG:-}" ]; then
  echo "PROJECT_USER_CONFIG is not set."
  echo "Example:"
  echo "export PROJECT_USER_CONFIG=configs/users/syed.yaml"
  exit 1
fi

echo "Using PROJECT_USER_CONFIG=${PROJECT_USER_CONFIG}"

MASTER_URL="${1:-}"

if [ -z "${MASTER_URL}" ]; then
  echo "Master URL argument is required."
  echo "Example:"
  echo "bash infra/aws/bootstrap/worker_bootstrap.sh spark://172.31.80.104:7077"
  exit 1
fi

export PATH="$HOME/.local/bin:$PATH"

echo "Syncing Python environment..."
uv sync

if [ ! -d "${SPARK_DIR}" ]; then
  echo "Installing Spark ${SPARK_VERSION}..."
  cd /tmp
  curl -fLo "${SPARK_TGZ}" "${SPARK_URL}"
  tar -xzf "${SPARK_TGZ}"
  sudo mv "${SPARK_ARCHIVE}" "${SPARK_DIR}"
else
  echo "Spark already installed at ${SPARK_DIR}"
fi

export SPARK_HOME="${SPARK_DIR}"
export PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

echo "Verifying Spark installation..."
spark-submit --version

echo "Stopping any existing Spark worker process..."
"${SPARK_HOME}/sbin/stop-worker.sh" || true

echo "Starting Spark worker..."
"${SPARK_HOME}/sbin/start-worker.sh" "${MASTER_URL}"

echo "Spark JVM status:"
jps || true

echo "Worker bootstrap complete."
echo "Connected worker to: ${MASTER_URL}"