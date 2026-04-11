# Data Flow Architecture — Wind Energy Forecasting Pipeline

This document describes the **end-to-end data flow** of the wind energy forecasting pipeline, from raw NOAA ISD data to modeling-ready datasets.

---

## Overview

The pipeline follows a layered architecture:

1. **Metadata Layer**
2. **Ingestion Layer (Raw Data)**
3. **Parsing Layer**
4. **Cleaning Layer**
5. **Storage Layer (Bronze → Silver → Gold)**
6. **Feature Engineering Layer**
7. **Modeling & Forecasting Layer**

---

## 1. Metadata Layer

### Source
- NOAA station metadata file: `isd-history.csv`

### Processing Steps

1. Load raw station metadata
2. Construct `station_id` using:
   - `USAF + WBAN`
3. Normalize fields:
   - latitude, longitude, elevation
   - begin/end dates

### Filtering Logic (Layer 1 Part B)

- Keep only `country_code = US`
- Remove invalid coordinates (`0,0` or nulls)
- Exclude:
  - Alaska (AK)
  - Hawaii (HI)
  - Territories (PR, GU, VI, AS, MP)
- Apply contiguous U.S. bounding box:
  - latitude: 24.5 → 49.5
  - longitude: -125 → -66
- Remove stations with missing state information
- Retain stations with valid active year metadata

### Output

**Station Master Table (~5,800–6,200 stations)**

Fields:
- station_id
- station_name
- state
- latitude
- longitude
- elevation_m
- begin_year
- end_year

This table defines the **geographic scope of the entire project**.

---

## 2. Ingestion Layer (Raw NOAA Data)

### Source
- S3 bucket: `noaa-global-hourly-pds`
- Format: CSV
- Partitioning: `year/station.csv`

### Characteristics

- Each file = **one station-year**
- Each row = **timestamped observation**
- Data is **wide and partially sparse**

### Ingestion Strategy

- Local sampling for development
- Distributed ingestion using Spark for scale
- Partition-aware reading (year-based)

---

## 3. Parsing Layer

### Problem

Core weather fields are **encoded strings**, not atomic values.

Examples:
- `WND = "324,1,H,0051,1"`
- `TMP = "+0093,1"`

### Parsing Tasks

- Split encoded fields into structured columns
- Extract:
  - wind speed (primary target)
  - wind direction
  - temperature
  - dew point
- Extract quality control (QC) flags

---

## 4. Cleaning Layer

### Key Rules

- Handle sentinel values:
  - `9999`, `+9999`, `99999` → NULL
- Apply QC filtering:
  - discard low-quality observations
- Standardize units:
  - wind speed → meters/second

### Output

Clean, validated weather observations ready for analysis.

---

## 5. Storage Layer

The pipeline follows a **medallion architecture**:

### Bronze Layer
- Raw structured data
- Minimal transformation
- Parsed but not cleaned

### Silver Layer
- Cleaned data
- QC-filtered
- Standardized units
- Joined with station metadata

### Gold Layer
- Aggregated and modeling-ready datasets
- Wind energy features
- Time-series aligned datasets

---

## 6. Feature Engineering Layer

Features include:

- Lag features (t-1, t-24, etc.)
- Rolling statistics (mean, std)
- Temporal features:
  - hour of day
  - day of week
  - seasonality

---

## 7. Modeling & Forecasting Layer

### Models

- Linear Regression
- Random Forest
- Gradient Boosted Trees

### Tasks

- Predict wind potential (derived from wind speed)
- Forecast 24–72 hours ahead

### Outputs

- Batch predictions
- Versioned model outputs
- Evaluation metrics

---

## Data Flow Summary

```

NOAA ISD (CSV, S3)
↓
Ingestion (Spark / local)
↓
Parsing (decode WND, TMP, etc.)
↓
Cleaning (QC + sentinel handling)
↓
Join with Station Master
↓
Silver Dataset (cleaned + enriched)
↓
Feature Engineering
↓
Gold Dataset (model-ready)
↓
ML Models → Forecasts

```

---

## Key Design Decisions

### 1. Use CSV Dataset (not raw ISD format)
- Avoid fixed-width parsing complexity
- Faster development

### 2. Local-first development
- Small samples used for iteration
- Scale later with Spark

### 3. Contiguous U.S. scope
- Reduces noise and complexity
- Aligns with wind energy use case

### 4. Wind-only focus
- `WND` is the primary modeling signal
- Other variables are secondary

---

## Current State (After Layer 1)

- Raw dataset structure understood
- Core columns defined
- Station metadata pipeline implemented
- Contiguous U.S. station master created
- Geographic and temporal coverage validated

---

## Next Steps

- Define development subset (Layer 1 Part C)
- Implement parsing logic for encoded fields
- Build Spark ingestion pipeline
- Develop cleaning and QC enforcement

---
