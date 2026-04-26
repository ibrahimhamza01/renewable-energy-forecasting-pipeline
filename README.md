# Wind Energy Forecasting Pipeline

A scalable, end-to-end **wind energy forecasting pipeline** built on NOAA Integrated Surface Database (ISD) data.  
Designed for **big data processing with PySpark**, **config-driven cloud execution**, and **reproducibility across local and distributed environments**.

---

## Project Goals

- Build an end-to-end **distributed data pipeline** for wind energy forecasting  
- Process NOAA ISD **hourly meteorological data (~600GB)** at scale using Spark  
- Convert raw weather observations into **wind energy potential estimates**  
- Develop **machine learning models** for short-term wind forecasting (24–72 hours)  
- Compare **distributed vs single-node systems** (Spark vs DuckDB)  
- Ensure **reproducibility across different users’ cloud environments (S3 + EC2)**  

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
- Always use the `DATE` column for time-based analysis  
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

src/            → core pipeline code
configs/        → shared + user-specific configs
configs/users/  → per-user AWS + local settings
data_contracts/ → schema + data definitions
infra/          → EC2, S3, Airflow setup
notebooks/      → validation + experiments
scripts/        → runnable entrypoints
tests/          → unit tests
docs/           → architecture, experiments, presentation materials
outputs/        → generated artifacts (gitignored)

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

This project is fully **config-driven** to support multiple users and environments.

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

# Current Status

## Layer 0 — Project Foundation

**Completed:**

* repository structure
* uv environment
* config system design
* initial data contracts

**Outcome:**

* consistent local development setup
* config-driven architecture (no hardcoding)
* structured, scalable project foundation

---

## Layer 1 — NOAA ISD Understanding and Scope Definition

**Key findings:**

* data organized as `year/station.csv`
* each file = station-year
* each row = timestamped observation

**Core encoded fields:**

* WND, TMP, DEW, VIS, CIG, SLP

**Sentinel values:**

* 9999, +9999, 99999, 999999

**Station filtering results:**

* total stations: 28,474
* U.S. stations: 7,074
* contiguous U.S.: 6,225
* valid stations (1995–2025): 4,943

**Modeling direction:**

* wind = primary target
* other fields = secondary

**Outcome:**

* raw schema understood
* geographic scope finalized
* modeling direction locked

---

## Layer 2 — Core Field Parsing Pipeline

**Implemented:**

* parsers for WND, TMP, DEW, VIS, CIG, SLP
* sentinel → NULL handling
* QC fields preserved
* safe parsing (no crashes)

**Pipeline:**

* local Spark pipeline
* Parquet output
* config-driven execution

**Validation:**

* notebooks + unit tests
* schema inspection
* null analysis
* numeric sanity checks

**Outcome:**

* reliable structured dataset from raw NOAA fields

---

## Layer 3 — Cleaning, QC Enforcement, Unit Standardization, Metadata Enrichment

**Cleaning:**

* QC filtering
* unit standardization (m/s, °C, hPa)
* timestamp normalization
* physical consistency checks

**Enrichment:**

* station metadata join
* geographic attributes (state, region)

**Validation:**

* unit tests
* notebook validation
* physical plausibility checks

**Outcome:**

* analysis-ready cleaned dataset

---

## Layer 4 — Cloud Runtime, EC2/S3/Spark Setup, User-Isolated Execution

**Implemented:**

* Spark cluster (master + workers) on EC2
* automated bootstrap scripts
* config-driven S3 path resolution
* Spark job submission via `spark-submit`
* S3A integration with IAM-based authentication

**Outcome:**

* fully operational distributed runtime
* reproducible cloud execution per user

---

## Layer 5 — Bronze and Silver Data Lake Creation at Scale

**Bronze Layer:**

* distributed ingestion of NOAA ISD CSV data from S3
* parallel processing of thousands of station-year files
* normalization of ingestion schema
* handling of missing NOAA files gracefully
* mitigation of small-file problem via compaction

**Output:**

```
s3a://<user-bucket>/bronze/isd
```

**Silver Layer:**

* distributed parsing of encoded NOAA fields
* QC enforcement at scale
* unit standardization (m/s, °C, hPa)
* enrichment with station metadata (~5,800 stations)
* partitioned Parquet writes

**Partitioning strategy:**

* year
* state

**Output:**

```
s3a://<user-bucket>/silver/weather
```

---

### Scaled Validation Results

**Dataset scale (full run 1995–2025):**

* Bronze rows: 35M+
* Silver rows: ~29M
* Retention rate: ~81%

**Data quality:**

* no nulls in critical fields (station_id, timestamp, state)
* wind speed distribution realistic
* no physically impossible values
* QC filtering effective

**Performance:**

* partition pruning efficient
* selective queries execute in seconds
* balanced partitions across states and years

---

### Outcome

* Bronze and Silver layers fully built for **1995–2025**
* scalable distributed ETL pipeline validated end-to-end
* Silver dataset established as **trusted source of truth**
* storage layout optimized for downstream analytics

---

## Input to Next Layer

* validated Silver dataset (1995–2025)
* ready for feature engineering and modeling

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use `DATE` for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling

---

## Final Note

This project follows a **production-grade data pipeline design**:

* local-first validation
* distributed execution readiness
* config-driven reproducibility
* strict modular layering
* wind-focused modeling objective
