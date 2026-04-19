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

---

#### Part A — EC2 Spark Environment Bootstrap

Implemented:

* `infra/aws/bootstrap/install_dependencies.sh`
* `infra/aws/bootstrap/master_bootstrap.sh`
* EC2 provisioning workflow

Capabilities:

* install system dependencies (Java, Python, uv)
* install Spark (3.5.6)
* configure environment automatically
* start Spark master + worker on EC2
* verify cluster via UI and CLI

Cluster setup:

```
EC2 Instance
 ├── Spark Master (7077)
 ├── Spark Worker
 └── Driver (spark-submit)
```

Validation:

* Spark UI accessible (port 8080)
* worker successfully registered
* test Spark job executed locally on cluster

Outcome:

* fully functional single-node Spark cluster on EC2

---

#### Part B — Config-Driven S3 Layout and Path Abstraction

Implemented:

* `configs/paths.yaml`
* `configs/users/*.yaml`
* `src/common/paths.py`
* `src/common/aws_utils.py`

Key design:

* separation of **source bucket (NOAA)** vs **project bucket**
* logical path abstraction layer
* no hardcoded S3 paths anywhere in pipeline

Path system:

* raw: `s3a://noaa-global-hourly-pds`
* bronze: `s3a://<user-bucket>/bronze/...`
* silver: `s3a://<user-bucket>/silver/...`
* gold: `s3a://<user-bucket>/gold/...`
* outputs: local filesystem (config-driven)

Capabilities:

* dynamic path resolution
* environment portability across users
* consistent S3 structure

Validation:

* path resolution tested
* S3 listing verified
* config switching confirmed

Outcome:

* fully config-driven cloud path system
* zero hardcoded infrastructure paths

---

#### Part C — Remote Job Submission and Smoke Tests

Implemented:

* `scripts/bootstrap_repo.sh`
* `scripts/run_spark_job.sh`
* `src/common/spark_utils.py`
* remote smoke test script

Capabilities:

* config-driven Spark submission
* dynamic master resolution
* dependency injection (`--packages`)
* S3A support via Hadoop AWS connector
* EC2 IAM role-based authentication

Key fix:

* added Hadoop AWS dependency:

  ```
  org.apache.hadoop:hadoop-aws:3.3.4
  ```
* switched to `s3a://` protocol

Validation:

* Spark job submitted remotely
* executor allocated successfully
* DataFrame operations executed
* Parquet written to S3

Verified output:

```
s3://syed-datsbd-s2026/bronze/isd/_smoke_test/
  _SUCCESS
  part-*.parquet
```

Outcome:

* fully validated cloud execution workflow
* Spark jobs run end-to-end on EC2
* data written correctly to S3

---

### Layer 4 Merge Checkpoint

Achieved:

* each user can run jobs on their own EC2 + S3
* all S3 paths are config-driven
* Spark jobs run remotely via `spark-submit`
* no hardcoded cloud identifiers remain
* environment is fully portable

---

### Completion Criteria (Achieved)

* working distributed runtime
* validated Spark cluster
* config-driven S3 integration
* successful remote execution pipeline

---

### Input to Next Layer

* working cloud runtime
* validated S3 integration
* ready for large-scale ingestion

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
