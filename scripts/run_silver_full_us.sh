#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_USER_CONFIG:?PROJECT_USER_CONFIG is not set}"

MODE="${1:?Usage: $0 <overwrite|append> <year1> [year2 ...]}"
shift

if [[ "$MODE" != "overwrite" && "$MODE" != "append" ]]; then
  echo "MODE must be overwrite or append"
  exit 1
fi

if [[ "$#" -lt 1 ]]; then
  echo "At least one year is required"
  exit 1
fi

python -m src.storage.write_silver \
  --years "$@" \
  --station-master-path outputs/station_master_contiguous_us.csv \
  --mode "$MODE"