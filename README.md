# Wind Energy Forecasting Pipeline

A scalable, end-to-end wind energy forecasting pipeline built on NOAA Integrated Surface Database (ISD) data.  
Designed for big data processing with PySpark, config-driven cloud execution, and reproducibility across local and distributed environments.

---

## Project Goals

- Build an end-to-end distributed data pipeline for wind energy forecasting
- Process NOAA ISD hourly meteorological data (~600GB) at scale using Spark
- Convert raw weather observations into wind energy potential estimates
- Develop machine learning models for short-term wind forecasting (24–72 hours)
- **Benchmark distributed vs single-node systems (Spark vs DuckDB)**
- Ensure reproducibility across different users’ cloud environments (S3 + EC2)
- **Orchestrate the entire pipeline using Apache Airflow (production-style scheduling layer)**

---

## Dataset: NOAA Integrated Surface Database (ISD)

- Source: NOAA ISD (AWS Open Data)
- Format: CSV (wide schema with encoded fields)
- Scale: 600GB+ uncompressed

### Coverage

- Global stations (~35,000)
- Hourly observations
- Years: 1901–2025

---

## Project Scope

### Geographic scope

- Contiguous U.S.

### Large-scale project window

- 1995–2025

### Local development subset

- states: CA, TX, MN, FL
- years: 2018–2020
- target size: ~150 stations

---

## Core Fields in Scope

- WND → wind speed & direction (primary target field)
- TMP → temperature
- DEW → dew point
- VIS → visibility
- CIG → ceiling
- SLP → pressure
- DATE → true timestamp (used for all time logic)

---

## Important Notes

- S3 file timestamps are not data timestamps
- Always use the DATE column for time-based analysis
- Many weather fields are encoded strings and require parsing
- The dataset is wide and sparse, so optional fields are excluded from v1
- Wind is the primary modeling target
- Auxiliary weather fields are secondary
- Solar is out of scope

---

## Tech Stack

- Python (uv-managed environment)
- PySpark (distributed processing)
- DuckDB (single-node benchmarking)
- Pandas / NumPy
- PyArrow
- AWS (S3, EC2)
- **Apache Airflow (orchestration layer)**
- Datashader / Plotly

---

## Repository Structure

```

src/             → core pipeline code
configs/         → shared + user-specific configs
configs/users/   → per-user AWS + local settings
data_contracts/  → schema + data definitions
infra/           → EC2, S3, Airflow setup
notebooks/       → validation + experiments
scripts/         → runnable entrypoints
tests/           → unit tests
docs/            → architecture, experiments, presentation materials
outputs/         → generated artifacts (gitignored)

```

---

## Setup (uv workflow)

### Install dependencies

```

uv sync

```

### Activate environment

```

source .venv/bin/activate

```

### Verify

```

which python

```

---

## Configuration System

This project is fully config-driven to support multiple users and environments.

❗ Never hardcode

- S3 bucket names
- EC2 hostnames
- Spark master URLs
- Local directories
- Output paths

---

### Configuration layers

#### 1. Shared config (configs/)

Defines:

- dataset paths
- Spark settings
- project defaults

Examples:

- configs/paths.yaml
- configs/spark_config.yaml

---

#### 2. User config (configs/users/<name>.yaml)

Defines:

- AWS project bucket
- EC2 host + SSH access
- Spark master URL
- local runtime paths

---

#### 3. Active config

```

export PROJECT_USER_CONFIG=configs/users/syed.yaml

```

---

## Development Workflow

1. Build locally on a small sample
2. Validate with notebooks and tests
3. Scale to Spark (EC2 + S3)
4. Re-validate outputs
5. **Orchestrate using Airflow DAGs**

---

## Pipeline Summary

```

raw NOAA data
→ parsing
→ cleaning
→ enrichment
→ aggregation
→ analytics
→ feature engineering
→ ML-ready data
→ model training
→ model registry
→ batch inference
→ forecast outputs
→ validation

```

---

# Data Processing and Outputs

## Raw Data Understanding

- Data organized as year/station.csv
- Each file = station-year
- Each row = timestamped observation

---

## Cleaning and Parsing

- Encoded fields parsed into numeric values
- Sentinel values (9999, +9999, etc.) → NULL
- Quality control filters applied
- Units standardized (m/s, °C, hPa)
- Station metadata joined for geographic context

---

# Data Lake Structure

## Bronze Layer

- Raw ingestion from NOAA S3
- Normalized ingestion schema
- Handles missing files
- Small-file problem mitigated

Output:

```

s3a://<user-bucket>/bronze/isd

```

---

## Silver Layer

- Parsed weather fields
- QC filtering
- Unit standardization
- Metadata enrichment

Partitioning:

- year
- state

Output:

```

s3a://<user-bucket>/silver/weather

```

---

# Wind Energy Modeling

## Wind Potential Definition

Wind potential is measured using capacity factor:

- normalized wind energy output between 0 and 1

---

## Wind Physics Modeling

- Turbine-inspired power curve
- Cut-in, rated, cut-out speeds
- Wind power density calculation
- Spark-native implementation (no Python UDFs)

---

# Final Analytical Tables (Gold Layer)

## Daily Regional Wind Table

```

s3a://<user-bucket>/gold/wind/analytics/daily_region

```

## Monthly State Wind Table

```

s3a://<user-bucket>/gold/wind/analytics/monthly_state

```

## Extreme Event Table

```

s3a://<user-bucket>/gold/wind/analytics/extreme_events

```

---

# Machine Learning Tables

## ML Base Table

```

s3a://<user-bucket>/gold/wind/ml/base

```

## Feature Table

Includes:

- Lag features
- Rolling statistics
- Temporal features
- Weather aggregates

---

## Training Tables

Time-based splits:

- Train ≤ 2019
- Validation 2020–2022
- Test ≥ 2023

---

# Model Training and Selection (Layer 9)

## Models

- Baseline
- Linear Regression
- Random Forest
- Gradient Boosted Trees (GBT)

---

## Best Model

```

final_tuned_gbt

```

---

## Performance

- RMSE ≈ 0.042
- MAE ≈ 0.025

---

## Model Registry

```

s3a://<user-bucket>/models/registry/

```

---

# Layer 10 — Batch Inference and Forecast Outputs

## Output Location

```

s3a://<user-bucket>/forecasts/outputs/

```

---

## Forecast Performance

- MAE ≈ 0.0275
- RMSE ≈ 0.0455
- Bias ≈ ~0

---

# Apache Airflow Orchestration (Layer 11)

## Overview

The pipeline is orchestrated using Apache Airflow to simulate a production-grade workflow.

---

## DAG: `wind_pipeline_dag`

### Tasks

1. check_config  
2. write_bronze  
3. write_silver  
4. build_gold_wind_tables  
5. build_feature_table  
6. train_model  
7. evaluate_model  
8. update_model_registry  
9. generate_forecasts  
10. validate_forecasts  

---

## Execution Modes

### Dry Run Mode (Safe)

Used for:

- Demonstration
- Testing DAG structure
- Avoiding heavy compute

Example:

```

echo "[DRY RUN] Skipping bronze layer"

```

---

### Full Run Mode (Production)

Executes actual scripts:

```

bash scripts/run_bronze_full_us.sh

```

---

## Observability

Airflow UI provides:

### Graph View

- Visual DAG structure
- Task dependencies
- Execution state (success/failure)

### Gantt View

- Task execution timeline
- Performance insights

### Logs

- Per-task execution details
- Debugging information

---

## Key Learnings

- Airflow executes tasks inside containers → file paths must exist inside container
- Logs are the primary debugging mechanism
- DAGs must support both dry-run and full execution
- Orchestration is separate from business logic
- Config-driven pipelines simplify multi-user environments

---

# Layer 12 — Benchmarking: DuckDB vs Spark

## Overview

This layer evaluates compute tradeoffs between single-node and distributed execution using representative pipeline workloads.

---

## Benchmark Tasks

- Filtering by year and region
- Daily regional wind aggregation
- Grouped temporal summaries
- (Optional) station metadata joins

All tasks are implemented with equivalent logic in both DuckDB and Spark.

---

## Implementation

### DuckDB (Single-node)

- Runs locally on exported Parquet subsets
- Optimized for fast analytical queries
- Minimal startup overhead

### Spark (Distributed)

- Runs on Spark (local or EC2 cluster)
- Includes job scheduling and execution overhead
- Designed for large-scale distributed workloads

---

## Benchmark Execution

Single command to run full benchmark pipeline:

```

./scripts/run_benchmarks.sh

```

Outputs:

```

outputs/benchmark_results/
├── duckdb_benchmarks.csv
├── spark_benchmarks.csv
├── benchmark_comparison.csv

```

---

## Key Results

- DuckDB significantly outperforms Spark on small local datasets
- Spark incurs startup and scheduling overhead
- Spark performance improves on warm runs
- Spark becomes necessary for large-scale S3-based processing

---

## Interpretation

- DuckDB is best for:
  - local analysis
  - development iteration
  - small-to-medium datasets

- Spark is best for:
  - large-scale distributed workloads
  - multi-year NOAA ISD processing
  - production pipelines and orchestration

---

# Key Rules

- All paths must come from config
- Code must be environment-agnostic
- Never hardcode infrastructure
- Always use true timestamps
- Validate before scaling
- Separate business logic from orchestration

---

# Final Note

This project implements a **production-grade data + ML + orchestration pipeline**:

- Local-first development
- Distributed Spark execution
- Config-driven reproducibility
- Strict modular layering
- Physics-informed modeling
- End-to-end ML + inference system
- **Airflow-based orchestration layer**
- **Cross-engine benchmarking (DuckDB vs Spark)**

---

# Output Capability

The pipeline produces:

- Scalable wind energy datasets
- ML-ready features
- Trained models
- Versioned model registry
- Production-style forecast outputs
- Benchmark comparison results
- **Orchestrated execution via Airflow DAGs**

---

# Ready For

- Forecasting systems
- Batch inference pipelines
- Airflow orchestration
- Visualization dashboards
- Real-world energy analysis
- Production deployment
