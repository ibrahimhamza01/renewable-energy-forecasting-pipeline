# Benchmark Plan — DuckDB vs Spark

## Goal

Evaluate compute tradeoffs between DuckDB and Apache Spark for the wind energy forecasting pipeline.

This benchmark compares single-node analytical execution against distributed execution using representative project workloads.

## Systems Compared

### DuckDB

Single-node analytical engine used for local benchmarking on exported Parquet subsets.

### Apache Spark

Distributed processing engine used for large-scale EC2/S3 execution.

## Benchmark Inputs

Benchmarks should run on the same logical dataset wherever possible.

Primary input:

- Silver weather table
- Gold daily regional wind table
- Station metadata table

Recommended benchmark scales:

1. Small local subset  
   - 4 states
   - 2018–2020
   - ~150 stations

2. Medium subset  
   - contiguous U.S.
   - limited year range

3. Large/full subset  
   - contiguous U.S.
   - 1995–2025

## Benchmark Tasks

### Task 1 — Filter by year and region

Purpose:

Measure partition pruning and selective scan performance.

Example workload:

- Filter observations for selected years
- Filter to selected states or regions
- Count rows
- Compute basic wind speed statistics

Metrics:

- runtime seconds
- rows scanned
- rows returned

---

### Task 2 — Daily regional wind aggregation

Purpose:

Measure grouped aggregation performance on project-critical analytics.

Example workload:

- Group by date and region
- Compute average wind speed
- Compute average wind potential / capacity factor
- Count contributing stations

Metrics:

- runtime seconds
- output row count
- aggregation grain correctness

---

### Task 3 — Station metadata join

Purpose:

Measure join performance between weather observations and station metadata.

Example workload:

- Join weather observations to station metadata
- Filter to contiguous U.S.
- Group by state or region

Metrics:

- runtime seconds
- joined row count
- null metadata rate

---

### Task 4 — Grouped temporal summaries

Purpose:

Measure performance for time-series summaries used in analytics and modeling.

Example workload:

- Group by year, month, state or region
- Compute average wind potential
- Compute min/max wind speed
- Compute station coverage

Metrics:

- runtime seconds
- output row count
- grouped summary correctness

## Fairness Rules

DuckDB and Spark benchmarks must use equivalent logic.

Rules:

- Use the same input data whenever possible
- Use the same filters
- Use the same grouping keys
- Use the same output columns
- Avoid Python row-wise logic
- Run each benchmark multiple times
- Record cold-run and warm-run behavior separately if possible
- Do not compare full Spark cluster execution against a tiny local DuckDB dataset without clearly labeling the scale difference

## Metrics to Collect

For each benchmark run, collect:

- engine: duckdb or spark
- benchmark task name
- input path
- input format
- dataset scale label
- start timestamp
- end timestamp
- runtime seconds
- output row count
- notes
- success/failure status

Optional metrics:

- memory usage
- Spark executor count
- Spark partitions
- DuckDB threads
- input data size
- output data size

## Expected Interpretation

DuckDB is expected to perform well for:

- local subsets
- interactive analysis
- single-node Parquet scans
- lightweight aggregations
- fast iteration during development

Spark is expected to perform better for:

- large multi-year datasets
- distributed S3 reads
- full contiguous U.S. processing
- large joins
- production pipeline execution
- repeatable EC2-scale workloads

## Benchmark Outputs

Recommended output directory:

```text
outputs/benchmark_results/
````

Recommended result files:

```text
outputs/benchmark_results/duckdb_benchmarks.csv
outputs/benchmark_results/spark_benchmarks.csv
outputs/benchmark_results/benchmark_comparison.csv
```

## Completion Criteria

This benchmark design is complete when:

* benchmark tasks are clearly defined
* DuckDB and Spark workloads are logically equivalent
* metrics are standardized
* result output format is agreed
* the comparison can support architecture claims in the final report