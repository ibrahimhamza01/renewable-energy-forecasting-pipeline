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

STATES="AL AR AZ CA CO CT DE FL GA IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY"

python -m src.ingestion.ingest_raw_isd \
  --years "$@" \
  --states $STATES \
  --station-master-path outputs/station_master_contiguous_us.csv \
  --target-files-per-year 100 \
  --mode "$MODE"