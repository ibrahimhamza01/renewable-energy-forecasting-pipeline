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
- **Contiguous U.S.**

### Large-scale project window
- **1995–2025**

### Local development subset
- states: **CA, TX, MN, FL**
- years: **2018–2020**
- target size: **~150 stations**

---

## Core Fields in Scope

- `WND` → wind speed & direction (**primary target field**)
- `TMP` → temperature
- `DEW` → dew point
- `VIS` → visibility
- `CIG` → ceiling
- `SLP` → pressure
- `DATE` → **true timestamp (used for all time logic)**

---

## Important Notes

- S3 file timestamps are **not** data timestamps  
- Always use the `DATE` column for time-based analysis  
- Many weather fields are **encoded strings** and require parsing  
- The dataset is **wide and sparse**, so optional fields are excluded from v1  
- Wind is the **primary modeling target**  
- Auxiliary weather fields are **secondary**  
- Solar is **out of scope**

---

## Tech Stack

- **Python (uv-managed environment)**
- **PySpark** (distributed processing)
- **DuckDB** (single-node benchmarking)
- **Pandas / NumPy**
- **PyArrow**
- **AWS (S3, EC2)**
- **Airflow** (planned)
- **Datashader / Plotly**

---

## Repository Structure

```text
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
```

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

This project is **fully config-driven** to support multiple users and environments.

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

## Current Status

---

### Layer 0 — Project Foundation

Completed:

* repository structure
* uv environment
* config system design
* initial data contracts

Key outcome:

* consistent local development setup
* config-driven architecture (no hardcoding)
* structured, scalable project foundation

---

### Layer 1 — NOAA ISD Understanding and Scope Definition

#### Part A — Raw dataset understanding

Key findings:

* data organized as **year/station.csv**
* each file = **station-year**
* each row = **timestamped observation**

Core encoded fields:

* `WND`, `TMP`, `DEW`, `VIS`, `CIG`, `SLP`

Sentinel values:

* `9999`, `+9999`, `99999`, `999999`

Outcome:

* raw schema understood
* core field scope fixed

---

#### Part B — Station filtering (contiguous U.S.)

Key results:

* total stations: **28,474**
* U.S. stations: **7,074**
* contiguous U.S.: **6,225**
* valid stations (1995–2025): **4,943**

Outcome:

* clean station master defined
* geographic scope finalized

---

#### Part C — Development subset + modeling direction

Key decisions:

* CA, TX, MN, FL
* 2018–2020
* ~150 stations

Modeling:

* wind = **primary target**
* other fields = **secondary**

Outcome:

* scope locked
* modeling direction finalized

---

### Layer 2 — Core Field Parsing Pipeline

#### Parsing

* implemented parsers for WND, TMP, DEW, VIS, CIG, SLP
* sentinel → NULL handling
* QC fields preserved
* safe parsing (no crashes)

#### Pipeline

* full local Spark pipeline
* Parquet output
* config-driven execution

#### Validation

* notebooks + unit tests
* schema inspection
* null analysis
* numeric sanity checks

Outcome:

* reliable structured dataset from raw NOAA fields

---

### Layer 3 — Cleaning, QC Enforcement, Unit Standardization, Metadata Enrichment

#### Cleaning

* QC filtering
* unit standardization (m/s, °C, hPa)
* timestamp normalization
* physical consistency checks

#### Enrichment

* station metadata join
* geographic attributes (state, region)

#### Validation

* unit tests
* notebook validation
* physical plausibility checks

Outcome:

* analysis-ready cleaned dataset

---

### Layer 4 — Cloud Runtime, EC2/S3/Spark Setup, User-Isolated Execution

#### Part A — EC2 Spark Environment Bootstrap

* Spark cluster (master + worker) on EC2
* automated bootstrap scripts
* validated Spark execution environment

#### Part B — Config-Driven S3 Layout

* logical path abstraction (`Paths`)
* separation of raw vs project buckets
* dynamic resolution of S3 paths

#### Part C — Remote Job Submission

* Spark jobs executed via `spark-submit`
* S3A integration (Hadoop AWS)
* IAM-based authentication

Outcome:

* fully operational distributed runtime
* reproducible cloud execution per user

---

### Layer 5 — Bronze and Silver Data Lake Creation at Scale

---

#### Part A — Raw Ingestion and Bronze Compaction

Implemented:

* distributed ingestion of NOAA ISD CSV files from S3
* parallel reading of thousands of station-year files
* normalization of raw ingestion schema
* handling of missing NOAA files gracefully
* mitigation of small-file problem via compaction

Capabilities:

* ingestion scaled across Spark executors
* robust handling of incomplete NOAA datasets
* efficient Parquet write to S3

Output:

* Bronze dataset written to:

```
s3a://<user-bucket>/bronze/isd
```

Outcome:

* scalable raw data lake layer established
* ingestion pipeline validated on distributed infrastructure

---

#### Part B — Parsing, Cleaning, Enrichment, Silver Writing at Scale

Implemented:

* distributed parsing of encoded NOAA fields
* QC enforcement at scale
* unit standardization (wind in m/s, temp in °C, pressure in hPa)
* join with station metadata (~5,800 stations)
* partitioned Parquet writes

Partitioning strategy:

* `year`
* `state`

Capabilities:

* large-scale transformation pipeline
* efficient partitioned storage layout
* optimized downstream read performance

Output:

```
s3a://<user-bucket>/silver/weather
```

Outcome:

* **analysis-ready silver dataset at scale**
* consistent schema across partitions
* enriched dataset with geographic attributes

---

#### Part C — Scaled ETL Validation and Performance Review

Validation performed via notebook:

```
notebooks/05_scaled_etl_validation.ipynb
```

##### Dataset scale

* Bronze rows: **35,504,907**
* Silver rows: **28,893,512**
* Retention rate: **~81%**

##### Partition validation

* years: **2018, 2019, 2020**
* states: **CA, TX, MN, FL**
* partitions balanced across states and years

##### Data quality checks

* no nulls in critical fields (`station_id`, `timestamp`, `state`)
* wind speed distribution realistic:

  * median: **3.1 m/s**
  * p95: **7.7 m/s**
  * max: **61.3 m/s**
* zero wind (~20%) consistent with real observations
* no physically impossible values detected

##### Schema validation

* schema stable across partitions
* required columns present
* correct data types enforced

##### Performance validation

* partition pruning works efficiently
* selective reads execute in ~1–2 seconds
* dataset suitable for downstream analytics

Outcome:

* silver dataset verified as **trusted source of truth**
* pipeline validated at scale
* ready for modeling and feature engineering

---

### Layer 5 Merge Checkpoint

Achieved:

* bronze and silver layers exist in S3
* silver dataset validated and trusted
* partitioning strategy confirmed effective
* distributed ETL pipeline fully operational

---

### Completion Criteria (Achieved)

* scalable ingestion pipeline
* distributed transformation pipeline
* validated silver data lake
* production-grade data quality checks
* performant partitioned storage

---

### Input to Next Layer

* validated silver weather dataset
* ready for feature engineering and modeling
* ready for full dataset scaling (1995–2025)

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use `DATE` for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling

---

## Final Note

This project follows a **production-grade pipeline design**:

* local-first validation
* distributed execution readiness
* config-driven reproducibility
* strict modular layering
* wind-focused modeling objective
