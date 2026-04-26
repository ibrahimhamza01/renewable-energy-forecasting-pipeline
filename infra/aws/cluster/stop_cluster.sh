#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while read -r IP; do
  echo "Stopping worker on $IP..."

  ssh -o StrictHostKeyChecking=no -i ~/.ssh/syed-datsbd-s2026.pem ubuntu@$IP "
    /opt/spark/sbin/stop-worker.sh || true
  " &
done < "${SCRIPT_DIR}/workers.txt"

wait
echo "All workers stopped."