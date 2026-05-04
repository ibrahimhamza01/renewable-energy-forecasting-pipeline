#!/usr/bin/env bash
set -euo pipefail

WEATHER_PATH="${WEATHER_PATH:-data/benchmark_input/silver_weather}"
METADATA_PATH="${METADATA_PATH:-}"
DATASET_SCALE="${DATASET_SCALE:-small}"
BENCHMARK_YEAR="${BENCHMARK_YEAR:-2020}"
BENCHMARK_STATE="${BENCHMARK_STATE:-TX}"
N_RUNS="${N_RUNS:-3}"
DUCKDB_OUTPUT_PATH="${DUCKDB_OUTPUT_PATH:-outputs/benchmark_results/duckdb_benchmarks.csv}"
SPARK_OUTPUT_PATH="${SPARK_OUTPUT_PATH:-outputs/benchmark_results/spark_benchmarks.csv}"
COMPARISON_OUTPUT_PATH="${COMPARISON_OUTPUT_PATH:-outputs/benchmark_results/benchmark_comparison.csv}"

mkdir -p outputs/benchmark_results

echo "Running DuckDB benchmarks..."
echo "Weather path: ${WEATHER_PATH}"
echo "DuckDB output path: ${DUCKDB_OUTPUT_PATH}"
echo "Spark output path: ${SPARK_OUTPUT_PATH}"
echo "Comparison output path: ${COMPARISON_OUTPUT_PATH}"
echo "Dataset scale: ${DATASET_SCALE}"
echo "Year: ${BENCHMARK_YEAR}"
echo "State: ${BENCHMARK_STATE}"
echo "Runs: ${N_RUNS}"

if [[ -n "${METADATA_PATH}" ]]; then
  python3 -m src.benchmarking.benchmark_duckdb \
    --weather-path "${WEATHER_PATH}" \
    --metadata-path "${METADATA_PATH}" \
    --output-path "${DUCKDB_OUTPUT_PATH}" \
    --dataset-scale "${DATASET_SCALE}" \
    --year "${BENCHMARK_YEAR}" \
    --state "${BENCHMARK_STATE}" \
    --n-runs "${N_RUNS}"
else
  python3 -m src.benchmarking.benchmark_duckdb \
    --weather-path "${WEATHER_PATH}" \
    --output-path "${DUCKDB_OUTPUT_PATH}" \
    --dataset-scale "${DATASET_SCALE}" \
    --year "${BENCHMARK_YEAR}" \
    --state "${BENCHMARK_STATE}" \
    --n-runs "${N_RUNS}"
fi

echo "DuckDB benchmarks complete."

echo "Running Spark benchmarks..."

python3 -m src.benchmarking.benchmark_spark \
  --weather-path "${WEATHER_PATH}" \
  --output-path "${SPARK_OUTPUT_PATH}" \
  --dataset-scale "${DATASET_SCALE}" \
  --year "${BENCHMARK_YEAR}" \
  --state "${BENCHMARK_STATE}" \
  --n-runs "${N_RUNS}"

echo "Building benchmark comparison report..."

python3 -m src.benchmarking.benchmark_report \
  --duckdb-path "${DUCKDB_OUTPUT_PATH}" \
  --spark-path "${SPARK_OUTPUT_PATH}" \
  --output-path "${COMPARISON_OUTPUT_PATH}"