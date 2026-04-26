#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/worker_ids.txt" ]; then
  echo "worker_ids.txt not found. Aborting."
  exit 1
fi

echo "Terminating worker instances:"
cat "${SCRIPT_DIR}/worker_ids.txt"

read -p "Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

aws ec2 terminate-instances \
  --instance-ids $(cat "${SCRIPT_DIR}/worker_ids.txt")

echo "Done."