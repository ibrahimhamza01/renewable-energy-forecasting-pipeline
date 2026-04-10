# Renewable Energy Forecasting Pipeline

Wind energy forecasting pipeline using NOAA ISD data, built with PySpark, DuckDB, and a config-driven architecture for reproducible cloud and local execution.

---

## Project Goals

- Build an end-to-end big data pipeline for wind energy forecasting
- Process NOAA ISD weather data at scale using Spark
- Compare distributed vs single-node systems (Spark vs DuckDB)
- Develop forecasting models for wind potential
- Ensure reproducibility across local and cloud environments

---

## Tech Stack

- Python (uv-managed environment)
- PySpark
- DuckDB
- Pandas / NumPy
- PyArrow
- AWS (S3, EC2)
- Airflow (later stage)
- Datashader / Plotly for visualization

---

## Repository Structure

```

src/            → core pipeline code
configs/        → shared + user-specific configs
data_contracts/ → schema + data definitions
infra/          → cloud + airflow setup
notebooks/      → validation + experiments
scripts/        → runnable entrypoints
tests/          → unit tests
docs/           → design + experiments
outputs/        → generated artifacts (ignored in git)

```

---

## Setup (uv workflow)

We use **uv** for dependency management. Do NOT use pip or requirements.txt.

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

## Configuration System (IMPORTANT)

This project uses a **layered config system**.

### DO NOT hardcode:

* S3 bucket names
* EC2 hostnames
* local file paths
* output locations

### Instead:

* Shared config → `configs/*.yaml`
* User config → `configs/users/<name>.yaml`
* Active config via env variable:

```bash
export PROJECT_USER_CONFIG=configs/users/<your_name>.yaml
```

---

## Development Workflow

1. Build locally (small data)
2. Validate with tests + notebooks
3. Run at scale on Spark/EC2
4. Validate outputs locally

---

## Team Structure

* Data Pipeline Lead → ingestion, parsing, cleaning, storage
* Platform Lead → config, AWS, Airflow, runtime
* Analytics Lead → validation, features, ML, benchmarking

---

## Current Status

Layer 0 — Project foundation (in progress)

* [x] Repo structure
* [x] uv environment
* [ ] Config system
* [ ] Data contracts

---

## Notes

* All paths must come from config
* Code must be environment-agnostic
* Avoid hardcoding anything infrastructure-related

---
