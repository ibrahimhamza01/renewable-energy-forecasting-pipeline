# Wind Energy Forecasting Pipeline

A scalable, end-to-end wind energy forecasting pipeline built on NOAA Integrated Surface Database (ISD) data.  
Designed for big data processing with PySpark, config-driven cloud execution, and reproducibility across local and distributed environments.

---

## Project Goals

- Build an end-to-end distributed data pipeline for wind energy forecasting  
- Process NOAA ISD hourly meteorological data (~600GB) at scale using Spark  
- Convert raw weather observations into wind energy potential estimates  
- Develop machine learning models for short-term wind forecasting (24–72 hours)  
- Compare distributed vs single-node systems (Spark vs DuckDB)  
- Ensure reproducibility across different users’ cloud environments (S3 + EC2)  

---

## Dataset: NOAA Integrated Surface Database (ISD)

- **Source:** NOAA ISD (AWS Open Data)  
- **Format:** CSV (wide schema with encoded fields)  
- **Scale:** 600GB+ uncompressed  

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
- Airflow (planned)  
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

````

---

## Setup (uv workflow)

### Install dependencies

```bash
uv sync
````

### Activate environment

```bash
source .venv/bin/activate
```

### Verify

```bash
which python
```

---

## Configuration System

This project is fully config-driven to support multiple users and environments.

### Never hardcode

* S3 bucket names
* EC2 hostnames
* Spark master URLs
* Local directories
* Output paths

---

### Configuration layers

#### 1. Shared config (`configs/`)

Defines:

* dataset paths
* Spark settings
* project defaults

Examples:

* `configs/paths.yaml`
* `configs/spark_config.yaml`

---

#### 2. User config (`configs/users/<name>.yaml`)

Defines:

* AWS project bucket
* EC2 host + SSH access
* Spark master URL
* local runtime paths

---

#### 3. Active config

```bash
export PROJECT_USER_CONFIG=configs/users/syed.yaml
```

---

## Development Workflow

1. Build locally on a small sample
2. Validate with notebooks and tests
3. Scale to Spark (EC2 + S3)
4. Re-validate outputs

---

## Pipeline Summary

This project implements a full data pipeline:

```
raw NOAA data → parsing → cleaning → enrichment → aggregation → analytics → ML-ready data
```

---

## Data Processing and Outputs

### Raw Data Understanding

* Data organized as `year/station.csv`
* Each file = station-year
* Each row = timestamped observation

### Cleaning and Parsing

* Encoded fields parsed into numeric values
* Sentinel values (9999, +9999, etc.) converted to NULL
* Quality control filters applied
* Units standardized (m/s, °C, hPa)
* Station metadata joined for geographic context

---

## Data Lake Structure

### Bronze Layer

* Raw ingestion from NOAA S3
* Normalized ingestion schema
* Handles missing files
* Small-file problem mitigated

Output:

```
s3a://<user-bucket>/bronze/isd
```

---

### Silver Layer

* Parsed weather fields
* QC filtering
* Unit standardization
* Metadata enrichment

Partitioning:

* year
* state

Output:

```
s3a://<user-bucket>/silver/weather
```

---

## Wind Energy Modeling

### Wind Potential Definition

Wind potential is measured using **capacity factor**, defined as:

> normalized wind energy output between 0 and 1

Interpretation:

* 0 → no usable wind
* ~0.05 → low/moderate wind
* ~0.10+ → strong wind
* ~0.30+ → very strong wind

---

### Wind Physics Modeling

* turbine-inspired power curve
* cut-in, rated, cut-out speeds
* wind power density calculation
* normalized output bounded in [0, 1]
* Spark-native implementation (no Python UDFs)

---

## Final Analytical Tables (Gold Layer)

### Daily Regional Wind Table

```
s3a://<user-bucket>/gold/wind/analytics/daily_region
```

* Grain: state-date
* Primary analysis table
* Used for:

  * stability analysis
  * distribution analysis
  * ML feature generation

---

### Monthly State Wind Table

```
s3a://<user-bucket>/gold/wind/analytics/monthly_state
```

* Grain: state-year-month
* Used for:

  * seasonal trends
  * geographic comparisons
  * presentation and reporting

---

### Extreme Event Table

```
s3a://<user-bucket>/gold/wind/analytics/extreme_events
```

* Identifies:

  * high wind (top 10%)
  * low wind (bottom 10%)
* Includes:

  * z-score normalization
  * state-specific thresholds

---

### ML Base Table

```
s3a://<user-bucket>/gold/wind/ml/base
```

* Target:

  * next-day wind potential
* Features:

  * lag features (1d, 7d)
  * rolling statistics
  * seasonal features
  * regional aggregates

---

## Dataset Scale (Final Outputs)

* states: 48
* years: 31 (1995–2025)

### Row counts

* daily region: 537,449
* monthly state: 17,664
* extreme events: 537,449
* ML base: 537,401

---

## Validation Results

### Range checks

* daily capacity factor: 0.0 → 0.900287
* monthly capacity factor: 0.001662 → 0.274203

### Data quality

* no null targets in ML table
* expected lag nulls (boundary effects only)
* no invalid physical values

### Extreme events

* high wind ≈ 10%
* low wind ≈ 10%
* normal ≈ 80%

---

## Key Insights

* Wind potential is **geographically concentrated** (Great Plains dominate)
* Wind follows a **strong seasonal cycle**
* Wind distribution is **right-skewed**
* Most days have moderate wind, extreme events are rare
* Wind is **predictable but not constant**, requiring forecasting

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use DATE / parsed timestamp fields for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling
* Validate sampled outputs before full-scale execution
* Keep business logic separate from storage/path logic

---

## Final Note

This project follows a production-grade data pipeline design:

* local-first validation
* distributed execution readiness
* config-driven reproducibility
* strict modular layering
* physically informed wind modeling
* scalable analytics and ML datasets

The pipeline produces **reliable, large-scale wind energy datasets** ready for:

* descriptive analysis
* visualization
* forecasting models
* real-world energy insights
