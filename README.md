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
  - Years: 1901–2025 (project subset: 1995–2025)

### Key Fields Used

- `WND` → wind speed & direction (**primary target**)
- `TMP` → temperature
- `DEW` → dew point
- `VIS` → visibility
- `CIG` → ceiling
- `SLP` → pressure
- `DATE` → **true timestamp (used for all time logic)**

### Important Notes

- S3 file timestamps are **NOT data timestamps**
- Always use the `DATE` column for time-based analysis
- Many fields are **encoded strings** and require parsing
- Dataset is **wide and sparse** (many optional columns ignored in v1)

---

## Tech Stack

- **Python (uv-managed environment)**
- **PySpark** (distributed processing)
- **DuckDB** (single-node benchmarking)
- **Pandas / NumPy**
- **PyArrow**
- **AWS (S3, EC2)**
- **Airflow** (pipeline orchestration, later stage)
- **Datashader / Plotly** (visualization)

---

## Repository Structure

```

src/            → core pipeline code (ETL, features, ML)
configs/        → shared + user-specific configs
configs/users/  → per-user AWS + local settings
data_contracts/ → schema + data definitions
infra/          → EC2, S3, Airflow setup
notebooks/      → validation + experiments
scripts/        → runnable entrypoints
tests/          → unit tests
docs/           → design + experiments
outputs/        → generated artifacts (gitignored)

````

---

## Setup (uv workflow)

We use **uv** for dependency management.

Do NOT use:
- pip
- requirements.txt

### 1. Install dependencies

```bash
uv sync
````

### 2. Activate environment

```bash
source .venv/bin/activate
```

### 3. Verify

```bash
which python
```

---

## Configuration System (CRITICAL)

This project is **fully config-driven** to support multiple teammates with different AWS setups.

---

## NEVER hardcode:

* S3 bucket names
* EC2 hostnames
* Spark master URLs
* Local directories
* Output paths

---

## Configuration Layers

### 1. Shared config (`configs/`)

Defines:

* logical dataset paths
* Spark settings
* project-wide defaults

Examples:

* `configs/paths.yaml`
* `configs/spark_config.yaml`

---

### 2. User config (`configs/users/<name>.yaml`)

Defines **your personal infrastructure**:

```yaml
aws:
  s3_bucket: syed-wind-project
  s3_base_prefix: dsan6000

ec2:
  ssh_host: ec2-xx-xx.compute-1.amazonaws.com

spark:
  master_url: spark://ec2-xx-xx:7077

local:
  data_root: /home/syed/data
```

Each teammate has their own file:

* `configs/users/syed.yaml`
* `configs/users/ege.yaml`
* `configs/users/alejandro.yaml`

---

### 3. Active config selection

Set this once:

```bash
export PROJECT_USER_CONFIG=configs/users/syed.yaml
```

Or inside `.env`:

```env
PROJECT_USER_CONFIG=configs/users/syed.yaml
```

---

## Mental Model

| File                        | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| `configs/paths.yaml`        | Logical dataset paths (bronze/silver/gold) |
| `configs/spark_config.yaml` | Spark tuning                               |
| `configs/users/*.yaml`      | User-specific AWS + EC2 + local setup      |
| `.env`                      | Active user config selection               |

---

## Example (Path Resolution)

### Shared config:

```yaml
datasets:
  silver_prefix: silver/weather
```

### User config:

```yaml
aws:
  s3_bucket: syed-wind-project
  s3_base_prefix: dsan6000
```

### Final resolved path:

```
s3://syed-wind-project/dsan6000/silver/weather
```

---

## Development Workflow

Follow this cycle for every layer:

1. Build locally (small sample)
2. Validate with tests + notebooks
3. Run at scale on Spark (EC2 + S3)
4. Validate outputs locally

---

## Pipeline Overview

1. **Ingestion**

   * Read NOAA ISD CSV data

2. **Parsing**

   * Decode encoded fields (`WND`, `TMP`, etc.)

3. **Cleaning**

   * Apply QC rules
   * Handle sentinel values (e.g., 9999)
   * Standardize units

4. **Storage**

   * Bronze → raw structured
   * Silver → cleaned + enriched
   * Gold → wind datasets

5. **Wind Modeling**

   * Apply turbine power curve
   * Compute wind potential

6. **Feature Engineering**

   * Lag features
   * Rolling statistics
   * Temporal features

7. **Machine Learning**

   * Train regression models
   * Predict wind potential

8. **Forecasting**

   * Batch predictions
   * Versioned outputs

9. **Orchestration**

   * Airflow DAGs

---

## Team Structure

* **Data Pipeline Lead**

  * ingestion, parsing, cleaning, storage

* **Platform Lead**

  * config system, AWS, Airflow, runtime

* **Analytics Lead**

  * validation, features, ML, benchmarking

---

## Current Status

### Layer 0 — Project Foundation ✅

* [x] Repo structure
* [x] uv environment
* [x] Config design (in progress)
* [x] Data contracts (initial)

### Layer 1 — Dataset Understanding 🔄

* [x] Part A: NOAA ISD inspection + schema definition
* [x] Part B: Station metadata + contiguous US filtering
* [ ] Part C: Development subset decision

#### Part B Output

* Built station metadata pipeline using NOAA `isd-history.csv`
* Created **contiguous U.S. station master (~5.8k–6.2k stations)**
* Filtering included:

  * U.S. stations only
  * valid coordinates
  * exclusion of Alaska, Hawaii, and territories
  * geographic bounding box
  * removal of missing state entries
* Verified geographic distribution and temporal coverage
* Identified ~4,900 stations active in 1995–2025 window

---

## Key Rules

* All paths must come from config
* Code must be environment-agnostic
* Always use `DATE` for time logic
* Never rely on S3 file timestamps
* Validate locally before scaling

---

## Final Note

This project is designed to mimic a **real-world production data pipeline**:

* Distributed processing (Spark)
* Cloud-native storage (S3)
* Config-driven reproducibility
* Orchestrated workflows (Airflow)
* ML model lifecycle and forecasting

---


