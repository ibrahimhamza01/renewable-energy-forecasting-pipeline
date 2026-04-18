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

This project is **config-driven** to support multiple users and environments.

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

#### 2. User config (`configs/users/<name>.yaml`)

Defines:

* S3 bucket
* EC2 host
* Spark master
* local paths

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
* config-driven design (no hardcoding)
* structured repository for layered development

---

### Layer 1 — NOAA ISD Understanding and Scope Definition

#### Part A — Raw dataset understanding

Key findings:

* data organized as **year/station.csv**

* each file = **station-year**

* each row = **timestamped observation**

* core encoded fields identified:

  * `WND`, `TMP`, `DEW`, `VIS`, `CIG`, `SLP`

* common sentinel patterns:

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

* local subset:

  * CA, TX, MN, FL
  * 2018–2020
  * ~150 stations

* modeling:

  * wind = **primary**
  * other fields = **secondary**

Outcome:

* scope locked
* modeling direction finalized

---

### Layer 2 — Core Field Parsing Pipeline

#### Part A — Parser implementation

Implemented parsers for:

* `WND` → wind direction, speed, QC
* `TMP` → temperature (tenths °C → °C)
* `DEW` → dew point
* `SLP` → pressure
* `VIS` → visibility
* `CIG` → ceiling

Design principles:

* schema-first parsing
* sentinel handling → NULL
* malformed input → safe fallback (no crashes)
* QC fields preserved (no filtering yet)

---

#### Part B — Pipeline integration

Files created:

* `parse_all_fields.py`
* `spark_utils.py`
* `run_local_sample_pipeline.py`
* `scripts/run_local_sample_pipeline.sh`

Capabilities:

* run full parsing pipeline locally
* write output as **Parquet**
* environment-safe Spark configuration
* no hardcoded paths

---

#### Part C — Validation and testing

Validation methods:

* notebook-based validation (`03_parse_validation.ipynb`)
* unit tests (`tests/test_parsers.py`)
* integration test for full pipeline
* schema inspection (`printSchema`)
* null distribution checks
* numeric sanity checks (min/max)

---

#### Key Observations

* encoded NOAA fields successfully converted to structured columns
* sentinel values consistently mapped to NULL
* malformed inputs handled without breaking pipeline
* QC flags preserved for downstream validation
* Spark returns decimals for scaled values (expected behavior)
* parsing layer is intentionally **non-strict** (semantic validation deferred)

---

#### Key Outcome

* reliable transformation from **raw encoded NOAA fields → structured weather features**
* stable, testable parsing layer
* reproducible local pipeline execution
* schema finalized for downstream processing

---

### Layer 3 — Cleaning, QC Enforcement, Unit Standardization, Metadata Enrichment

#### Goal

Transform parsed weather observations into **analysis-ready data** suitable for wind energy modeling.

---

#### Part A — Cleaning and Unit Standardization

Files implemented:

* `src/cleaning/quality_filters.py`
* `src/cleaning/standardize_units.py`
* `src/cleaning/clean_isd.py`

Key logic implemented:

* QC flag filtering across all core weather fields
* invalid value removal using domain bounds
* sentinel-to-null handling for all measurements
* wind speed conversion to **meters per second (m/s)**
* temperature and dew point conversion to **°C**
* pressure conversion to **hPa**
* timestamp normalization → `timestamp_utc`, `date_utc`, and time components
* basic consistency checks:

  * dew point ≤ temperature
* wind-focused usability filtering:

  * `has_valid_wind_speed`
  * `has_valid_timestamp`
  * `is_core_row_complete`
  * `is_wind_row_usable`

Key design decisions:

* strict QC enforcement (invalid values dropped, not imputed)
* wind speed quality prioritized as primary modeling signal
* cleaning applied before unit conversion
* audit and diagnostic flags retained for transparency

---

#### Part B — Metadata Enrichment and Local Output

Files implemented:

* `src/cleaning/enrich_with_station_metadata.py`
* `src/common/io_utils.py`
* `configs/paths.yaml`
* `src/cleaning/run_local_sample_pipeline.py`
* updated `scripts/run_local_sample_pipeline.sh`

Key capabilities:

* join cleaned weather data with station metadata
* derive geographic attributes:

  * `state`
  * `region` (U.S. region mapping)
* attach station attributes:

  * station name
  * latitude / longitude
  * elevation
* config-driven path resolution:

  * no hardcoded local or output paths
* write cleaned enriched dataset as **Parquet**

Output:

* `outputs/sample_runs/cleaned_enriched_sample`

---

#### Part C — Data Quality Validation

Files implemented:

* `notebooks/04_cleaning_validation.ipynb`
* `tests/test_quality_filters.py`
* `tests/test_unit_conversions.py`
* updated `data_contracts/quality_flag_rules.md`

Validation checks performed:

* missingness after cleaning
* wind data usability validation
* unit correctness across all weather fields
* physical plausibility checks:

  * wind speed
  * temperature
  * pressure
  * visibility
  * ceiling height
* consistency validation:

  * dew point ≤ temperature
* station metadata coverage:

  * join correctness
  * region derivation

Testing:

* QC filter unit tests → **all passed**
* unit conversion tests → **all passed**
* end-to-end pipeline validation using local sample runs

---

#### Key Observations

* cleaning pipeline successfully removes low-quality observations
* remaining data is physically consistent and modeling-ready
* wind-focused filtering ensures high-quality wind signals
* metadata enrichment correctly attaches geographic context
* cleaned dataset is stable and reproducible

---

#### Key Outcome

* transformation from parsed data → **cleaned, enriched weather dataset**
* reliable wind speed measurements in m/s
* validated QC rules and data contracts
* trusted local dataset ready for modeling

---

#### Layer 3 Merge Checkpoint

* cleaned schema is fixed and stable
* wind speed in m/s is reliable
* QC enforcement validated through tests
* metadata joins are correct
* cleaned local outputs are trusted

---

#### Completion Criteria (Achieved)

* an analysis-ready weather dataset
* reliable wind observations for modeling
* validated cleaning and QC logic
* reproducible local pipeline outputs

---

#### Input to Next Layer

* cleaned enriched weather data
* validated QC rules and transformations

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use `DATE` for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling

---

## Final Note

This project follows a production-style pipeline design:

* local-first validation
* distributed execution readiness
* config-driven reproducibility
* strict scope control
* wind-focused modeling objective
