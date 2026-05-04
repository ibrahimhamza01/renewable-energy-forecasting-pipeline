#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-dry-run}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -z "${PROJECT_USER_CONFIG:-}" ]; then
  export PROJECT_USER_CONFIG="configs/users/syed.yaml"
fi

case "${MODE}" in
  dry-run)
    export DRY_RUN=true
    echo "Starting Airflow in DRY_RUN mode"
    ;;

  full-run)
    export DRY_RUN=false
    echo "Starting Airflow in FULL_RUN mode"
    echo "WARNING: this may launch real Spark jobs"
    ;;

  stop)
    echo "Stopping Airflow"
    sudo docker compose down
    exit 0
    ;;

  reset)
    echo "Resetting Airflow containers and DB"
    sudo docker compose down -v
    rm -rf infra/airflow/db
    mkdir -p infra/airflow/db
    sudo chown -R 50000:0 infra/airflow/db
    exit 0
    ;;

  *)
    echo "Usage:"
    echo "  bash scripts/run_airflow.sh dry-run"
    echo "  bash scripts/run_airflow.sh full-run"
    echo "  bash scripts/run_airflow.sh stop"
    echo "  bash scripts/run_airflow.sh reset"
    exit 1
    ;;
esac

mkdir -p infra/airflow/db
sudo chown -R 50000:0 infra/airflow/db

echo "PROJECT_USER_CONFIG=${PROJECT_USER_CONFIG}"
echo "DRY_RUN=${DRY_RUN}"

sudo -E docker compose up -d airflow-init
sudo -E docker compose up -d

echo
echo "Airflow is running."
echo "Open: http://<EC2_PUBLIC_IP>:8081"
echo "Login: admin / admin"