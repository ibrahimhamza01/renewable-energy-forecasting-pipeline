# Website Content Draft

# Hero Section

## Title

Live Wind Forecasting Platform

## Subtitle

A production-style distributed data engineering and machine learning platform for estimating and forecasting U.S. wind energy potential using NOAA Integrated Surface Database (ISD) observations.

## Hero Metrics

- 600GB+ NOAA ISD dataset
- 35,000+ global weather stations
- 30 years of hourly observations
- Spark + Airflow + ML pipeline
- Distributed Bronze/Silver/Gold architecture
- Live NOAA-powered wind estimation

## Hero CTA Buttons

- Explore Live Wind
- View Pipeline
- See Forecast Results
- GitHub Repository

---

# Overview Page

## Section: Project Motivation

Renewable energy systems depend heavily on weather variability.

This project builds a scalable distributed pipeline for estimating and forecasting wind energy potential across the United States using multi-decade NOAA weather observations.

The system combines:

- distributed Spark ETL
- medallion-style data lake architecture
- Airflow orchestration
- feature engineering
- machine learning forecasting
- live NOAA-powered wind estimation

---

## Section: Dataset

### NOAA Integrated Surface Database (ISD)

- Source: NOAA Open Data
- Scale: 600GB+
- Coverage: 1901–2025
- Resolution: hourly observations
- Stations: 35,000+ globally

Core weather fields:

- WND
- TMP
- DEW
- VIS
- CIG
- SLP

---

## Section: Architecture Summary

Pipeline flow:

```text
NOAA Raw Data
→ Bronze Layer
→ Silver Layer
→ Gold Analytics
→ Feature Engineering
→ ML Training
→ Model Registry
→ Forecast Outputs
→ Website Artifacts
````

Core technologies:

* PySpark
* Airflow
* DuckDB
* AWS S3
* EC2
* Parquet
* XGBoost
* FastAPI
* Next.js

---

# Live Wind Explorer Page

## Purpose

Provide a live wind potential estimate using current NOAA/NWS observations and turbine-inspired power-curve logic.

## Live Inputs

* wind speed
* wind direction
* temperature
* station metadata

## Output Metrics

* live wind speed
* estimated capacity factor
* power curve operating point
* estimated wind potential category

## Supported Stations

Initial supported stations:

* KSFO
* KIAH
* KMSP
* KMIA

---

# Pipeline Architecture Page

## Key Sections

### Bronze Layer

Raw NOAA ingestion and compaction.

### Silver Layer

Parsing, cleaning, QC filtering, and metadata enrichment.

### Gold Layer

Wind potential aggregation and analytical datasets.

### Feature Engineering

Lag features, rolling statistics, temporal indicators.

### Machine Learning

Gradient Boosted Trees forecasting workflow.

### Orchestration

Apache Airflow DAG execution.

### Benchmarking

DuckDB vs Spark analytical comparison.

---

# Wind Potential Results Page

## Planned Visuals

* U.S. wind potential map
* seasonal trends
* regional wind trends
* station map
* long-term temporal patterns

## Supporting Narrative

The Spark pipeline converts NOAA weather observations into physically informed wind potential estimates across regions and seasons.

---

# Forecasting Page

## Planned Metrics

### Final Model

Gradient Boosted Trees (GBT)

### Metrics

* RMSE ≈ 0.042
* MAE ≈ 0.025
* low prediction bias

## Planned Visuals

* forecast vs actual
* prediction distributions
* feature importance
* temporal forecast trends

---

# Benchmarking Page

## Purpose

Demonstrate why distributed processing was necessary.

## Key Findings

### DuckDB

* excellent local analytical performance
* fast iteration
* low startup overhead

### Spark

* scalable distributed execution
* suitable for large NOAA workloads
* necessary for multi-decade processing

---

# Final Takeaways Page

## Engineering Takeaways

* distributed ETL is required for large NOAA workloads
* config-driven infrastructure improves reproducibility
* Airflow orchestration improves operational structure
* Spark enables scalable analytics and ML workflows

## Modeling Takeaways

* wind potential varies strongly by region and season
* physically informed modeling improves interpretability
* engineered temporal features improve forecasting quality

## Product Takeaways

* historical Spark outputs can power durable static products
* live NOAA integrations create interactive portfolio experiences
* distributed pipelines can be extended into deployable products

---

# Footer Content

## Links

* GitHub Repository
* Project Report
* NOAA ISD Dataset
* Live API Status

## Footer Summary

Built using Spark, Airflow, AWS, NOAA ISD, FastAPI, and Next.js.
