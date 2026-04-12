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
- Coverage:
  - Global stations (~35,000)
  - Hourly observations
  - Years: 1901–2025

### Project Scope

- Geographic scope: **contiguous U.S.**
- Large-scale project window: **1995–2025**
- Local development subset:
  - states: **CA, TX, MN, FL**
  - years: **2018–2020**
  - target size: **~150 stations**

### Core Fields in Scope

- `WND` → wind speed & direction (**primary target field**)
- `TMP` → temperature
- `DEW` → dew point
- `VIS` → visibility
- `CIG` → ceiling
- `SLP` → pressure
- `DATE` → **true timestamp (used for all time logic)**

### Important Notes

- S3 file timestamps are **not** data timestamps
- Always use the `DATE` column for time-based analysis
- Many weather fields are **encoded strings** and will require parsing
- The dataset is **wide and sparse**, so many optional columns are excluded from the v1 core scope
- Wind is the **primary modeling target**
- Sparse auxiliary weather fields are **secondary**
- Solar is **out of scope**

---

## Tech Stack

- **Python (uv-managed environment)**
- **PySpark** (distributed processing)
- **DuckDB** (single-node benchmarking)
- **Pandas / NumPy**
- **PyArrow**
- **AWS (S3, EC2)**
- **Airflow** (planned orchestration layer)
- **Datashader / Plotly** (visualization)

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

We use **uv** for dependency management.

Do **not** use:

* `pip`
* `requirements.txt`

### 1. Install dependencies

```bash
uv sync
```

### 2. Activate environment

```bash
source .venv/bin/activate
```

### 3. Verify

```bash
which python
```

---

## Configuration System

This project is **config-driven** to support multiple teammates with different AWS setups.

### Never hardcode

* S3 bucket names
* EC2 hostnames
* Spark master URLs
* Local directories
* Output paths

### Configuration layers

#### 1. Shared config (`configs/`)

Defines:

* logical dataset paths
* Spark settings
* project-wide defaults

Examples:

* `configs/paths.yaml`
* `configs/spark_config.yaml`

#### 2. User config (`configs/users/<name>.yaml`)

Defines personal infrastructure settings such as:

* S3 bucket
* S3 prefix
* EC2 host
* Spark master URL
* local data root

#### 3. Active config selection

```bash
export PROJECT_USER_CONFIG=configs/users/syed.yaml
```

or in `.env`:

```env
PROJECT_USER_CONFIG=configs/users/syed.yaml
```

---

## Development Workflow

Follow this cycle for every layer:

1. Build locally on a small sample
2. Validate with notebooks and checks
3. Scale later to Spark (EC2 + S3)
4. Re-validate outputs locally

---

## Current Status

### Layer 0 — Project Foundation (Complete)

Completed:

* repository structure
* uv environment
* config system design
* initial data contracts

Key outcome:

* the project now has a consistent local development setup
* cloud-specific values are intended to be config-driven rather than hardcoded
* the repo structure is organized for layered development

---

### Layer 1 — NOAA ISD Understanding and Development Scope (Complete)

Completed:

* raw dataset inspection and field behavior study
* station metadata loading and contiguous U.S. filtering
* development subset and wind-only viability decision

#### Part A — Raw dataset inspection and field behavior study

Files created/updated:

* `src/ingestion/discover_isd_files.py`
* `notebooks/01_dataset_understanding.ipynb`
* `configs/schema/isd_raw_schema.json`

Main findings:

* NOAA ISD CSV data is organized as **`year/station.csv`**
* each file represents a **station-year**
* each row is a **timestamped weather observation**
* core encoded weather fields consistently observed:

  * `WND`
  * `CIG`
  * `VIS`
  * `TMP`
  * `DEW`
  * `SLP`
* common sentinel and missing patterns observed:

  * `9999`
  * `+9999`
  * `99999`
  * `999999`
* extra fields such as `CALL_SIGN` and `REM` were observed but treated as non-core
* many optional encoded field families were found to be sparse or inconsistent and were excluded from the v1 core scope

Key outcome:

* the raw NOAA ISD row structure is understood
* the core raw field scope is fixed

#### Part B — Station metadata and contiguous U.S. scope filtering

Files created/updated:

* `src/ingestion/station_metadata_loader.py`
* `src/ingestion/station_filter.py`
* `notebooks/02_station_scope_and_coverage.ipynb`
* `docs/architecture/data_flow.md`

Main findings:

* station metadata was loaded from NOAA `isd-history.csv`
* contiguous U.S. filtering required more than `country_code = US`
* geographic filtering and state filtering were both needed
* stations with invalid coordinates or missing state information had to be removed

Filtering summary:

* total metadata stations loaded: **28,474**
* U.S. stations: **7,074**
* valid-coordinate U.S. stations: **7,052**
* after excluding Alaska, Hawaii, and territories: **6,432**
* contiguous U.S. stations: **6,225**
* stations overlapping `1995–2025`: **4,943**

Key outcome:

* a clean contiguous U.S. station master was defined
* retained station metadata includes:

  * station_id
  * latitude
  * longitude
  * elevation
  * state
  * active year range

#### Part C — Development subset and viability decision for wind-only project

Files created/updated:

* `docs/experiments/dataset_viability.md`
* `docs/presentation/question_map.md`
* `notebooks/02_station_scope_and_coverage.ipynb`

Main findings:

* selected local development states:

  * **CA**
  * **TX**
  * **MN**
  * **FL**
* station counts in selected states:

  * CA: **492**
  * TX: **490**
  * FL: **301**
  * MN: **204**
* stations in selected states overlapping `1995–2025`: **1,162**
* stations in selected states overlapping `2018–2020`: **630**

Development subset decision:

* local development subset:

  * states: **CA, TX, MN, FL**
  * years: **2018–2020**
  * target size: **~150 stations**
* large-scale project scope:

  * contiguous U.S.
  * years: **1995–2025**

Modeling scope decision:

* wind is the **primary** modeling focus
* `WND` plus station metadata is sufficient to support a wind-focused project
* `TMP`, `DEW`, `SLP`, `VIS`, and `CIG` are secondary supporting fields
* solar is **out of scope**

Key outcome:

* contiguous U.S. station scope is fixed
* core columns are fixed
* development subset is fixed
* wind-only direction is approved internally

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use `DATE` for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling

---

## Final Note

This project is being developed as a staged, production-style data pipeline:

* local-first validation
* later distributed execution
* config-driven reproducibility
* clear scope control
* focused wind forecasting objective

