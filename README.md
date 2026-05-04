# Wind Energy Forecasting Pipeline

A scalable, end-to-end wind energy forecasting pipeline built on NOAA Integrated Surface Database (ISD) data.  
Designed for big data processing with PySpark, config-driven cloud execution, and reproducibility across local and distributed environments.

---

# Project Goals

- Build an end-to-end distributed data pipeline for wind energy forecasting  
- Process NOAA ISD hourly meteorological data (~600GB) at scale using Spark  
- Convert raw weather observations into wind energy potential estimates  
- Develop machine learning models for short-term wind forecasting (24–72 hours)  
- Compare distributed vs single-node systems (Spark vs DuckDB)  
- Ensure reproducibility across different users’ cloud environments (S3 + EC2)

---

# Dataset: NOAA Integrated Surface Database (ISD)

- **Source:** NOAA ISD (AWS Open Data)  
- **Format:** CSV (wide schema with encoded fields)  
- **Scale:** 600GB+ uncompressed  

## Coverage

- Global stations (~35,000)  
- Hourly observations  
- Years: 1901–2025  

---

# Project Scope

## Geographic scope

- Contiguous U.S.

## Large-scale project window

- 1995–2025

## Local development subset

- states: CA, TX, MN, FL  
- years: 2018–2020  
- target size: ~150 stations  

---

# Core Fields in Scope

- WND → wind speed & direction (primary target field)  
- TMP → temperature  
- DEW → dew point  
- VIS → visibility  
- CIG → ceiling  
- SLP → pressure  
- DATE → true timestamp (used for all time logic)  

---

# Important Notes

- S3 file timestamps are **not** data timestamps  
- Always use the **DATE column** for time-based analysis  
- Many weather fields are encoded strings and require parsing  
- The dataset is wide and sparse, so optional fields are excluded from v1  
- Wind is the primary modeling target  
- Auxiliary weather fields are secondary  
- Solar is out of scope  

---

# Tech Stack

- Python (uv-managed environment)  
- PySpark (distributed processing)  
- DuckDB (single-node benchmarking)  
- Pandas / NumPy  
- PyArrow  
- AWS (S3, EC2)  
- Airflow (planned)  
- Datashader / Plotly  

---

# Repository Structure

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

# Setup (uv workflow)

## Install dependencies

```

uv sync

```

## Activate environment

```

source .venv/bin/activate

```

## Verify

```

which python

```

---

# Configuration System

This project is fully config-driven to support multiple users and environments.

## ❗ Never hardcode

- S3 bucket names  
- EC2 hostnames  
- Spark master URLs  
- Local directories  
- Output paths  

---

## Configuration layers

### 1. Shared config (`configs/`)

Defines:

- dataset paths  
- Spark settings  
- project defaults  

Examples:

- `configs/paths.yaml`  
- `configs/spark_config.yaml`  

---

### 2. User config (`configs/users/<name>.yaml`)

Defines:

- AWS project bucket  
- EC2 host + SSH access  
- Spark master URL  
- local runtime paths  

---

### 3. Active config

```

export PROJECT_USER_CONFIG=configs/users/syed.yaml

```

---

# Development Workflow

1. Build locally on a small sample  
2. Validate with notebooks and tests  
3. Scale to Spark (EC2 + S3)  
4. Re-validate outputs  

---

# Pipeline Summary

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

```

---

# Data Processing and Outputs

## Raw Data Understanding

- Data organized as `year/station.csv`  
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

**Output:**

```

s3a://<user-bucket>/bronze/isd

```

---

## Silver Layer

- Parsed weather fields  
- QC filtering  
- Unit standardization  
- Metadata enrichment  

**Partitioning:**

- year  
- state  

**Output:**

```

s3a://<user-bucket>/silver/weather

```

---

# Wind Energy Modeling

## Wind Potential Definition

Wind potential is measured using **capacity factor**, defined as:

- normalized wind energy output between 0 and 1  

---

## Interpretation

- 0 → no usable wind  
- ~0.05 → low/moderate wind  
- ~0.10+ → strong wind  
- ~0.30+ → very strong wind  

---

## Wind Physics Modeling

- Turbine-inspired power curve  
- Cut-in, rated, cut-out speeds  
- Wind power density calculation  
- Normalized output bounded in [0, 1]  
- Spark-native implementation (no Python UDFs)  

---

# Final Analytical Tables (Gold Layer)

## Daily Regional Wind Table

```

s3a://<user-bucket>/gold/wind/analytics/daily_region

```

- Grain: state-date  
- Primary analysis table  

---

## Monthly State Wind Table

```

s3a://<user-bucket>/gold/wind/analytics/monthly_state

```

---

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

---

## Feature Table

```

s3a://<user-bucket>/gold/wind/ml/features

```

Includes:

- Lag features  
- Rolling statistics  
- Temporal features  
- Weather aggregates  

---

## Training Tables

```

train / validation / test

```

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

## Goal

Generate reusable, production-style wind forecasts and persist them as versioned outputs.

---

## Part A — Forecast Generation

- Load latest approved model  
- Load feature inputs  
- Generate next-day forecasts  
- Standardize schema  

---

## Part B — Forecast Output Writing

### Output Location

```

s3a://<user-bucket>/forecasts/outputs/

```

### Versioning Structure

```

run_id=<timestamp>/
model_version=<model_id>/
part-*.parquet
_SUCCESS

```

### Schema

- forecast_id  
- forecast_date  
- state  
- region  
- target_name  
- prediction  
- model_name  
- model_version  
- generation_timestamp  
- horizon_days  

---

## Part C — Forecast QA and Validation

### Validations Performed

- Schema completeness (no missing columns)  
- Non-null checks (critical fields)  
- Prediction range validation (0–1 bounds)  
- Distribution checks (percentiles, variance)  
- State-level sanity checks  
- Comparison with actual observed values  

---

## Forecast Performance (Validation Results)

- MAE ≈ 0.0275  
- RMSE ≈ 0.0455  
- Bias ≈ ~0 (near-zero systematic error)  

---

## Key Observations

- Predictions fall within valid physical bounds  
- Distribution is right-skewed (expected for wind)  
- Strong alignment with actuals across states  
- No major bias or drift detected  
- Regional variation matches known wind patterns  

---

# Dataset Scale (Final Outputs)

- states: 48  
- years: 1995–2025  

Rows:

- forecasts: ~535,961  
- dates: 11,167  

---

# Key Insights

- Wind potential is geographically concentrated (Great Plains dominate)  
- Strong seasonal patterns exist  
- Wind distribution is highly skewed  
- Forecasts are accurate but inherently noisy  
- Temporal features dominate predictive power  

---

# Key Rules

- All paths must come from config  
- Code must be environment-agnostic  
- Never hardcode infrastructure  
- Always use true timestamps  
- Validate before scaling  
- Separate business logic from storage  

---

# Final Note

This project implements a **production-grade data + ML pipeline**:

- Local-first development  
- Distributed Spark execution  
- Config-driven reproducibility  
- Strict modular layering  
- Physics-informed modeling  
- End-to-end ML + inference system  

---

# Output Capability

The pipeline produces:

- Scalable wind energy datasets  
- ML-ready features  
- Trained models  
- Versioned model registry  
- Production-style forecast outputs  

---

# Ready For

- Forecasting systems  
- Batch inference pipelines  
- Airflow orchestration (next layer)  
- Visualization dashboards  
- Real-world energy analysis  
- Production deployment  
