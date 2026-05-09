# Wind Energy Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![PySpark](https://img.shields.io/badge/PySpark-Distributed-orange)]()
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20EC2-yellow)]()
[![Airflow](https://img.shields.io/badge/Airflow-Orchestration-red)]()
[![DuckDB](https://img.shields.io/badge/DuckDB-Benchmarking-lightgrey)]()
[![Next.js](https://img.shields.io/badge/Next.js-Live%20Website-black)]()
[![NOAA](https://img.shields.io/badge/NOAA-Live%20Weather%20API-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Planned%20Inference-green)]()
[![Status](https://img.shields.io/badge/Status-Active-success)]()

A production-style renewable energy forecasting platform built on NOAA Integrated Surface Database (ISD) data.

This project combines:

- large-scale distributed data engineering
- Spark-based ETL pipelines
- physics-informed wind energy modeling
- machine learning forecasting
- Apache Airflow orchestration
- cross-engine benchmarking
- analytical visualization
- static website artifact preservation
- live NOAA-powered wind estimation
- and a portfolio-grade web platform for demonstrating both historical analytics and live wind potential

The platform was designed to simulate a realistic end-to-end data + ML system capable of operating across local development, distributed cloud infrastructure, orchestration workflows, and deployable analytics interfaces.

---

# Project Objectives

The primary goals of this project are:

- build a scalable distributed forecasting pipeline using PySpark
- process NOAA ISD weather observations (~600GB+) efficiently
- convert raw meteorological observations into wind energy potential estimates
- engineer ML-ready forecasting datasets
- train and evaluate forecasting models for short-term wind prediction
- compare distributed vs single-node execution systems
- orchestrate workflows using Apache Airflow
- maintain reproducibility across users and environments
- generate analytical datasets and visual artifacts
- preserve final outputs so the project survives without EC2/S3
- build a live web interface using current NOAA/NWS observations
- package the entire system into a deployable portfolio-grade product

---

# High-Level Architecture

```mermaid
flowchart LR

A["NOAA ISD Data<br/>AWS Open Data"] --> B["Bronze Layer<br/>Raw Ingestion"]
B --> C["Silver Layer<br/>Parsing + Cleaning + QC"]
C --> D["Gold Layer<br/>Analytics + ML Tables"]

D --> E["Feature Engineering"]
E --> F["ML Training"]
F --> G["Model Registry"]
G --> H["Batch Forecasting"]
H --> I["Forecast Outputs"]

D --> J["Visualization Datasets"]
J --> K["Plots + Maps + Reporting"]

D --> W1["Website Artifact Exports"]
W1 --> W2["Static Website Data<br/>CSV + JSON + Images"]

E --> L["DuckDB Benchmarks"]
E --> M["Spark Benchmarks"]

N["Apache Airflow"] --> B
N --> C
N --> D
N --> E
N --> F
N --> H

P["NOAA/NWS Live API"] --> Q["Live Wind Explorer"]
W2 --> Q
Q --> R["Live Capacity Factor Estimate"]
````

---

# Dataset: NOAA Integrated Surface Database (ISD)

Source:

* NOAA ISD (AWS Open Data)

Characteristics:

* hourly global weather observations
* ~35,000 stations
* years: 1901–2025
* encoded wide-schema CSV format
* 600GB+ uncompressed scale

The dataset is large enough to require distributed processing for full-scale execution, but the project also supports local development on smaller subsets.

---

# Project Scope

## Geographic Scope

Contiguous United States.

The processed pipeline station universe currently covers:

* 48 states
* 2,419 processed pipeline stations
* 1,981 verified live NOAA/NWS stations mapped from processed station metadata

---

## Full Pipeline Window

1995–2025

---

## Local Development Scope

Development subset used for rapid iteration:

* California
* Texas
* Minnesota
* Florida

Years:

* 2018–2020

Approximate station scope:

* ~150 stations

---

# Core Weather Fields

The pipeline focuses on NOAA ISD weather fields relevant to wind forecasting.

| Field | Purpose                    |
| ----- | -------------------------- |
| WND   | wind speed + direction     |
| TMP   | temperature                |
| DEW   | dew point                  |
| VIS   | visibility                 |
| CIG   | ceiling                    |
| SLP   | sea-level pressure         |
| DATE  | true observation timestamp |

---

# Important Engineering Constraints

Several important NOAA ISD characteristics influenced the pipeline design.

## Timestamp Handling

S3 object timestamps are not valid analytical timestamps.

All time logic uses:

```text
DATE
```

from the NOAA observations.

This rule is important because object storage metadata represents file upload or modification time, not the actual weather observation time.

---

## Encoded Weather Fields

Many NOAA fields are encoded string payloads that require custom parsing logic.

The project includes dedicated parsers for:

* WND
* TMP
* DEW
* VIS
* CIG
* SLP

These parsers convert NOAA encoded fields into typed, analysis-ready columns.

---

## Sparse Wide Dataset

The ISD dataset is extremely wide and sparse.

Version 1 intentionally focuses on:

* wind forecasting
* essential weather features
* scalable processing
* usable analytical outputs

rather than exhaustive coverage of every NOAA field.

---

# Technology Stack

## Distributed Processing

* PySpark
* Spark SQL
* Parquet

---

## Data Science

* Pandas
* NumPy
* PyArrow

---

## Machine Learning

* Spark MLlib
* Gradient Boosted Trees
* Random Forest
* Linear Regression

---

## Cloud Infrastructure

* AWS S3
* AWS EC2

---

## Workflow Orchestration

* Apache Airflow

---

## Benchmarking

* DuckDB
* Spark

---

## Visualization

* Plotly
* Datashader
* Matplotlib
* exported static figures

---

## Website Platform

* Next.js
* TypeScript
* Tailwind CSS
* NOAA/NWS Weather API
* static CSV/JSON artifacts
* live browser-side wind estimation

---

## Planned Backend Inference Service

* FastAPI
* XGBoost portable inference
* model service deployment
* Render / Railway / Fly.io

---

# Repository Structure

```text
configs/               → runtime + Spark + website configuration
data/                  → raw samples + benchmark inputs
data_contracts/        → schema + mapping definitions

docs/
├── architecture/      → system architecture and cloud execution docs
├── experiments/       → ETL, Airflow, modeling, and benchmark experiments
├── presentation/      → presentation and website planning materials
├── website/           → website product and deployment planning docs
└── assets/            → exported website-safe figures and images

infra/                 → AWS + Airflow infrastructure
notebooks/             → validation + EDA + experiments
outputs/               → generated figures + metrics + local artifacts
reports/               → final written reports
scripts/               → runnable orchestration + ETL + export scripts
src/                   → core pipeline source code
tests/                 → validation + unit tests
website_data/          → exported website-ready datasets

website/
├── public/
│   ├── assets/        → static figures used by the web app
│   └── data/          → frontend-safe CSV/JSON artifacts
├── src/
│   ├── app/           → Next.js app routes
│   ├── components/    → reusable UI components
│   ├── lib/           → NOAA client, station loading, power curve logic
│   └── types/         → TypeScript data contracts
└── tests/             → planned frontend utility tests

README.md
FINAL_REPORT.pdf
docker-compose.yml
pyproject.toml
uv.lock
```

---

# Source Code Organization

## Ingestion

```text
src/ingestion/
```

Handles:

* NOAA file discovery
* station filtering
* metadata loading
* raw ingestion

---

## Parsing

```text
src/parsing/
```

Contains dedicated parsers for NOAA encoded weather fields.

---

## Cleaning

```text
src/cleaning/
```

Handles:

* QC filtering
* null normalization
* sentinel value handling
* metadata enrichment
* unit standardization

---

## Storage

```text
src/storage/
```

Responsible for:

* bronze writes
* silver writes
* gold table generation
* repartitioning
* compaction

---

## Feature Engineering

```text
src/features/
```

Builds:

* lag features
* rolling statistics
* temporal features
* regional features

---

## Physics Modeling

```text
src/physics/
```

Implements:

* turbine-inspired power curves
* wind indices
* capacity factor logic

using Spark-native expressions.

---

## Machine Learning

```text
src/ml/
```

Contains:

* training pipelines
* tuning workflows
* dataset splitting
* inference logic
* model registry utilities

---

## Benchmarking

```text
src/benchmarking/
```

Implements:

* Spark benchmarks
* DuckDB benchmarks
* benchmark reporting

---

## Visualization

```text
src/visualization/
```

Generates:

* wind maps
* trend charts
* forecast validation plots
* seasonal visualizations

---

## Reporting

```text
src/reporting/
```

Exports:

* metrics
* reporting artifacts
* website-ready summaries

---

## Website Frontend

```text
website/src/
```

Implements:

* live NOAA station explorer
* station data loading
* live observation fetching
* power curve estimation
* interactive web UI
* static artifact consumption

Current important website files:

```text
website/src/lib/noaaClient.ts
website/src/lib/powerCurve.ts
website/src/lib/stationData.ts
website/src/types/station.ts
website/src/components/LiveWindExplorer.tsx
website/src/components/PowerCurveChart.tsx
website/src/app/live/page.tsx
```

---

# Setup

## Install Dependencies

```bash
uv sync
```

---

## Activate Environment

```bash
source .venv/bin/activate
```

---

## Verify Environment

```bash
which python
```

---

# Website Setup

The website is a separate Next.js application inside:

```text
website/
```

## Install Website Dependencies

```bash
cd website
npm install
```

---

## Run Website Locally

```bash
npm run dev
```

The local development server opens at:

```text
http://localhost:3000
```

The live wind explorer is available at:

```text
http://localhost:3000/live
```

---

## Website Verification Commands

During development, keep this running:

```bash
npm run dev
```

Use this after important TypeScript changes:

```bash
npx tsc --noEmit
```

Use this before considering a website milestone complete or before deployment:

```bash
npm run build
```

Normal workflow:

```text
edit code → browser auto-refreshes
```

Final verification workflow:

```bash
npx tsc --noEmit
npm run build
```

---

# Configuration System

The pipeline is fully config-driven to support:

* multiple users
* different AWS environments
* local execution
* distributed execution
* reproducibility
* website artifact export

---

## Never Hardcode

The project intentionally avoids hardcoding:

* S3 buckets
* EC2 hostnames
* Spark URLs
* runtime paths
* output directories
* website artifact paths

---

## Shared Configs

Located in:

```text
configs/
```

Includes:

* Spark settings
* runtime defaults
* schemas
* modeling configs
* website configs
* deployment configs
* project paths

---

## User Configs

Located in:

```text
configs/users/
```

Defines:

* AWS resources
* EC2 access
* runtime locations
* Spark master URLs

---

## Active Runtime Config

```bash
export PROJECT_USER_CONFIG=configs/users/syed.yaml
```

---

# Development Workflow

The project follows a scalable development pattern.

1. build locally on small samples
2. validate with notebooks + tests
3. scale to Spark cluster execution
4. validate distributed outputs
5. orchestrate via Airflow
6. export analytical artifacts
7. preserve portable website datasets
8. build live website features
9. package for deployment

---

# End-to-End Pipeline Flow

```text
raw NOAA ingestion
→ parsing
→ cleaning
→ enrichment
→ standardization
→ aggregation
→ analytics
→ feature engineering
→ ML-ready datasets
→ model training
→ model evaluation
→ model registry
→ batch inference
→ forecast validation
→ visualization exports
→ website-ready artifact generation
→ live NOAA web integration
```

---

# Data Processing

## Raw NOAA Structure

NOAA ISD data organization:

```text
year/station.csv
```

Each file represents:

* a station-year

Each row represents:

* a timestamped weather observation

---

# Cleaning and Quality Control

The cleaning stage performs:

* sentinel value replacement
* malformed record handling
* numeric parsing
* metadata joins
* quality filtering
* unit normalization

Examples:

```text
9999
+9999
```

converted into:

```text
NULL
```

---

# Data Lake Architecture

## Bronze Layer

Purpose:

* raw NOAA ingestion
* normalized ingestion schema
* resilient distributed loading

Output:

```text
s3a://<user-bucket>/bronze/isd
```

---

## Silver Layer

Purpose:

* parsed weather fields
* quality-controlled records
* standardized units
* metadata enrichment

Partitioning:

* year
* state

Output:

```text
s3a://<user-bucket>/silver/weather
```

---

## Gold Layer

Purpose:

* analytical datasets
* ML-ready datasets
* forecasting aggregates
* benchmark-ready tables

Gold outputs power downstream analytics, model training, forecast validation, visualization exports, and website-ready artifacts.

---

# Wind Energy Modeling

## Wind Potential Definition

Wind potential is represented using:

```text
capacity factor
```

normalized between:

```text
0 and 1
```

Capacity factor represents estimated normalized wind energy output. A value of 0 means no estimated output, and a value near 1 means rated output.

---

## Physics-Based Modeling

The project includes turbine-inspired wind logic:

* cut-in speed
* rated speed
* cut-out speed
* wind power density estimation
* capacity factor estimation

All implemented using Spark-native transformations in the data pipeline.

No Python UDFs are used in production ETL logic.

---

## Power Curve Used by the Website

The live website implements the same simplified turbine-inspired power curve concept in TypeScript:

| Wind Speed Range | Interpretation                                        |
| ---------------- | ----------------------------------------------------- |
| below 3 m/s      | below cut-in, estimated output is 0                   |
| 3–12 m/s         | ramp-up region, output increases nonlinearly          |
| 12–25 m/s        | rated region, estimated output is near full           |
| above 25 m/s     | turbine cuts out to protect equipment in extreme wind |

This allows live NOAA wind observations to be converted into an estimated capacity factor directly in the browser.

---

# Gold Analytical Outputs

## Daily Regional Wind Table

```text
s3a://<user-bucket>/gold/wind/analytics/daily_region
```

---

## Monthly State Wind Table

```text
s3a://<user-bucket>/gold/wind/analytics/monthly_state
```

---

## Extreme Event Table

```text
s3a://<user-bucket>/gold/wind/analytics/extreme_events
```

---

# Machine Learning Pipeline

## ML Base Table

```text
s3a://<user-bucket>/gold/wind/ml/base
```

---

## Feature Engineering

Feature generation includes:

* lag features
* rolling statistics
* temporal features
* weather aggregates
* regional features

---

## Dataset Splits

Time-based splitting strategy:

| Split      | Years     |
| ---------- | --------- |
| Train      | ≤ 2019    |
| Validation | 2020–2022 |
| Test       | ≥ 2023    |

---

# Forecasting Models

Models evaluated:

* Baseline
* Linear Regression
* Random Forest
* Gradient Boosted Trees (GBT)

---

# Final Selected Model

```text
final_tuned_gbt
```

---

# Forecasting Performance

| Metric | Value  |
| ------ | ------ |
| RMSE   | ~0.042 |
| MAE    | ~0.025 |

---

## Forecast vs Actual

![Forecast vs Actual](./outputs/figures/forecast_vs_actual.png)

---

# Model Registry

```text
s3a://<user-bucket>/models/registry/
```

---

# Batch Inference Outputs

Forecast outputs stored in:

```text
s3a://<user-bucket>/forecasts/outputs/
```

---

# Forecast Validation Metrics

| Metric | Value   |
| ------ | ------- |
| MAE    | ~0.0275 |
| RMSE   | ~0.0455 |
| Bias   | ~0      |

---

# Apache Airflow Orchestration

The project includes a production-style orchestration layer using Apache Airflow.

Main DAG:

```text
wind_pipeline_dag
```

---

## DAG Responsibilities

* config validation
* bronze ingestion
* silver generation
* gold table generation
* feature table generation
* model training
* evaluation
* model registration
* forecast generation
* validation

---

## Airflow Execution Modes

### Dry Run Mode

Used for:

* demonstrations
* DAG validation
* safe orchestration testing

---

### Full Execution Mode

Runs actual distributed workloads.

Example:

```bash
bash scripts/run_bronze_full_us.sh
```

---

# Airflow Observability

The Airflow environment supports:

* Graph View
* Gantt View
* task logs
* dependency tracing
* execution monitoring

---

## Airflow DAG Graph

![Airflow DAG](./docs/experiments/airflow/airflow_dag_graph_success.png)

---

# Benchmarking: DuckDB vs Spark

The project benchmarks:

* single-node analytical execution

vs

* distributed Spark execution

using equivalent workloads.

---

# Benchmark Tasks

Included benchmark operations:

* filtering
* aggregations
* grouped summaries
* metadata joins

---

# Benchmark Results

Key findings:

* DuckDB performs exceptionally well on smaller local workloads
* Spark incurs scheduling overhead
* Spark becomes necessary at larger distributed scales
* warm Spark runs improve performance

---

# Benchmark Outputs

```text
outputs/benchmark_results/
├── duckdb_benchmarks.csv
├── spark_benchmarks.csv
├── benchmark_comparison.csv
```

---

# Final Visual Outputs

## U.S. Wind Potential Map

![U.S. Wind Potential Map](./outputs/figures/us_wind_potential_map.png)

---

## Regional Wind Trends

![Regional Wind Trends](./outputs/figures/regional_wind_trends.png)

---

## Seasonal Wind Trends

![Seasonal Wind Trends](./outputs/figures/seasonal_trends.png)

---

# Website Artifact Preservation

To ensure the project remains functional even after EC2/S3 expiration, portable frontend-safe artifacts are exported locally.

Current preserved artifacts include:

## Website Data Exports

```text
website/public/data/
├── all_pipeline_stations.json
├── feature_importance.json
├── forecast_vs_actual.csv
├── live_station_api_verification_audit.json
├── live_station_list.json
├── live_station_mapping_audit.csv
├── model_metrics.json
├── pipeline_summary.json
├── regional_trends.csv
├── seasonal_trends.csv
├── us_wind_station_map.csv
└── verified_live_station_list.json
```

---

## Website Asset Exports

```text
website/public/assets/
├── airflow_dag_graph_success.png
├── forecast_vs_actual.png
├── regional_wind_trends.png
├── seasonal_trends.png
└── us_wind_potential_map.png
```

---

## Artifact Validation

Validation scripts ensure:

* all exported images exist
* CSV schemas are readable
* JSON files are valid
* frontend datasets remain lightweight
* portable artifacts remain deployable
* station artifacts are available for website use

---

# How the Processed Pipeline Data Is Used in the Website

The live website is not only calling a public weather API. It is built on top of the processed Spark pipeline outputs.

The website currently uses processed pipeline data in the following ways.

---

## 1. Processed Station Universe

The website uses:

```text
website/public/data/us_wind_station_map.csv
```

and:

```text
website/public/data/all_pipeline_stations.json
```

to represent the station universe produced by the pipeline.

These files come from the processed wind station map export, not directly from the live NOAA API.

They contain:

* processed station IDs
* latitude
* longitude
* state
* historical average wind speed
* pipeline source labels

Current coverage:

| Artifact                    | Count     |
| --------------------------- | --------- |
| processed pipeline stations | 2,419     |
| state coverage              | 48 states |

This means the website station layer is grounded in the stations that passed the pipeline’s filtering, enrichment, and aggregation process.

---

## 2. Historical Wind Context

The station details shown in the live explorer include:

```text
Historical avg wind speed
```

This value comes from the processed pipeline export.

It is not provided by the NOAA live observation endpoint.

This lets the website show both:

* current live wind speed
* historical average wind speed from the pipeline

for the selected station.

---

## 3. ISD to ICAO/NWS Station Mapping

The pipeline station IDs are NOAA ISD-style identifiers.

The NOAA/NWS live API expects ICAO/NWS-style station identifiers such as:

```text
KSFO
KMSP
KIAH
KMIA
```

To bridge this gap, the project builds a mapping layer:

```text
ISD station ID
→ NOAA station metadata
→ ICAO/NWS station ID
→ live NOAA endpoint
```

This mapping produces:

```text
website/public/data/live_station_list.json
website/public/data/verified_live_station_list.json
website/public/data/live_station_mapping_audit.csv
website/public/data/live_station_api_verification_audit.json
```

Current live station coverage:

| Artifact                         | Count     |
| -------------------------------- | --------- |
| ICAO/NWS candidate live stations | 2,040     |
| verified live NOAA stations      | 1,981     |
| verified live state coverage     | 48 states |

This is why the live explorer can support nationwide live station search instead of only a small manually selected list.

---

## 4. Live Station Verification

The project verifies candidate live stations by checking the NOAA/NWS endpoint:

```text
https://api.weather.gov/stations/{stationId}/observations/latest
```

Only stations that respond successfully are exported into:

```text
website/public/data/verified_live_station_list.json
```

The frontend uses this verified list for the live explorer.

This prevents the UI from presenting stations that are unlikely to work with live NOAA observations.

---

## 5. Forecast and Model Artifacts

The website preserves model and forecast outputs from the pipeline:

```text
website/public/data/forecast_vs_actual.csv
website/public/data/model_metrics.json
website/public/data/feature_importance.json
```

These artifacts support planned or current website sections for:

* forecast validation
* model performance
* feature importance
* forecasting results

---

## 6. Trend and Map Artifacts

The website preserves analytical exports:

```text
website/public/data/regional_trends.csv
website/public/data/seasonal_trends.csv
website/public/data/us_wind_station_map.csv
```

These support website sections for:

* regional wind trends
* seasonal capacity factor patterns
* station-level wind potential maps

---

## 7. Static Figures

The website also uses pipeline-generated figures:

```text
website/public/assets/forecast_vs_actual.png
website/public/assets/regional_wind_trends.png
website/public/assets/seasonal_trends.png
website/public/assets/us_wind_potential_map.png
website/public/assets/airflow_dag_graph_success.png
```

These are generated from the analysis and visualization layers, then copied into frontend-safe static assets.

---

# Live NOAA Wind Estimator

The website currently includes a working live wind estimator.

Route:

```text
/live
```

Implemented files:

```text
website/src/lib/noaaClient.ts
website/src/lib/powerCurve.ts
website/src/lib/stationData.ts
website/src/components/LiveWindExplorer.tsx
website/src/components/PowerCurveChart.tsx
website/src/app/live/page.tsx
website/src/types/station.ts
```

---

## What the Live Estimator Does

The live estimator:

1. loads verified live stations from local website artifacts
2. allows filtering by state
3. allows searching by station code, name, or state
4. fetches the latest NOAA/NWS live observation
5. extracts:

   * wind speed
   * wind direction
   * temperature
   * observation timestamp
6. converts live wind speed into estimated capacity factor
7. displays the operating point on a turbine power curve
8. shows observation metadata and observation age
9. handles NOAA API failures with a fallback state

---

## What Comes from NOAA Live API

The live NOAA/NWS API provides:

* current wind speed
* current wind direction
* current temperature
* observation timestamp

The endpoint used is:

```text
https://api.weather.gov/stations/{stationId}/observations/latest
```

---

## What Comes from the Pipeline

The pipeline provides:

* station universe
* station coordinates
* state filtering
* historical average wind speed
* ISD to ICAO/NWS station mapping
* live station verification inputs
* trend artifacts
* map artifacts
* model metrics
* forecast validation artifacts

The website combines both systems:

```text
processed historical Spark pipeline artifacts
+
live NOAA/NWS observations
+
power curve estimation
```

---

## What the Live Estimator Is Not Yet

The live estimator is not yet:

* live Spark inference
* live GBT inference
* real-time feature engineering
* streaming prediction
* deployed backend ML inference

Those are planned for the future model service layer.

The current live feature is a real-time physics-based wind potential estimator using live NOAA observations and the project’s turbine power-curve methodology.

---

# Testing

The repository includes unit and validation tests for:

* parsers
* unit conversions
* feature generation
* model IO
* quality filters
* power curve logic

Test suite location:

```text
tests/
```

---

# Current Website Platform Work

The project is currently being extended into a live portfolio-grade forecasting platform.

Current website capabilities include:

* Next.js application setup
* static asset preservation
* website-ready CSV/JSON exports
* verified nationwide live station list
* live NOAA observation fetcher
* browser-side power curve estimation
* live station search and filtering
* fallback state for NOAA API failures

Planned capabilities include:

* interactive forecasting dashboards
* pipeline storytelling pages
* benchmark visualizations
* deployable ML inference
* public cloud deployment

---

# Planned Website Stack

## Frontend

* Next.js
* TypeScript
* Tailwind CSS
* Plotly / Chart.js

---

## Backend

* FastAPI
* XGBoost portable inference
* NOAA Weather API integration

---

## Deployment

* Vercel
* Render / Railway

---

# Website Product Direction

The website separates:

## Historical Pipeline Results

Precomputed artifacts exported from Spark:

* trends
* forecasts
* metrics
* benchmark outputs
* visualizations
* station metadata

from

## Live Wind Estimation

Real-time NOAA weather observations combined with:

* turbine-inspired power curve logic
* verified station mappings
* optional deployable ML inference in the future

This ensures the platform remains functional even if EC2/S3 infrastructure expires.

---

# Current Website Planning Docs

```text
docs/website/
├── data_export_plan.md
├── deployment_plan.md
├── live_prediction_design.md
└── product_spec.md
```

---

# Engineering Principles

Core project rules:

* all paths must come from config
* infrastructure must remain environment-agnostic
* timestamps must use true NOAA observation times
* orchestration must remain separate from business logic
* validation occurs before scaling
* portable artifacts should outlive cloud infrastructure
* website data must be lightweight and deployable
* live claims must be technically honest

---

# Final Outcome

This project demonstrates:

* distributed data engineering
* scalable ETL architecture
* Spark-based processing
* ML forecasting systems
* Airflow orchestration
* benchmarking methodology
* reproducible infrastructure
* analytical visualization
* website-ready artifact preservation
* nationwide live NOAA station integration
* live physics-based wind estimation
* production-style packaging
* deployable forecasting platform design

---

# Ready For

* forecasting systems
* renewable energy analytics
* distributed ETL pipelines
* Airflow orchestration
* ML engineering workflows
* analytical dashboards
* live forecasting interfaces
* production deployment
* technical portfolio demonstrations
