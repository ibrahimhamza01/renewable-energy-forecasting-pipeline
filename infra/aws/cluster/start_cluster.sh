#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MASTER_URL="spark://ip-172-31-83-109.ec2.internal:7077"

while read -r IP; do
  echo "Starting worker on $IP..."

  ssh -o StrictHostKeyChecking=no -i ~/.ssh/syed-datsbd-s2026.pem ubuntu@$IP "
  set -e

  if [ ! -d ~/renewable-energy-forecasting-pipeline ]; then
    echo 'Cloning repo on worker...'
    git clone https://github.com/ibrahimhamza01/renewable-energy-forecasting-pipeline.git ~/renewable-energy-forecasting-pipeline
  fi

  cd ~/renewable-energy-forecasting-pipeline

  export PROJECT_USER_CONFIG=configs/users/syed.yaml

  echo 'Bootstrapping worker...'
  bash infra/aws/bootstrap/worker_bootstrap.sh $MASTER_URL
" &
done < "${SCRIPT_DIR}/workers.txt"

wait
echo "All workers started."