# Question Map — Wind Energy Forecasting Pipeline

This document maps key project questions to data, methods, and pipeline components.

It is intended for:
- presentations
- project framing
- stakeholder communication

---

## 1. Core Project Question

### Q1: Can we forecast short-term wind energy potential using historical weather observations?

**Approach:**
- Use NOAA ISD hourly weather data
- Extract wind speed from `WND`
- Train models to predict future wind conditions (24–72 hours)

**Data required:**
- wind speed (primary)
- timestamp (`DATE`)
- station metadata (location)

---

## 2. Data Understanding Questions

### Q2: What is the structure of NOAA ISD data?

**Answer:**
- CSV format
- partitioned by `year/station.csv`
- each row = timestamped observation
- core fields are encoded (e.g., `WND`, `TMP`, `DEW`)

---

### Q3: Which fields are reliable and usable?

**Answer:**
- Core fields:
  - `WND`
  - `TMP`
  - `DEW`
  - `VIS`
  - `CIG`
  - `SLP`
- Many optional fields (`AA*`, `CN*`, etc.) are sparse and excluded

---

### Q4: What is the geographic scope?

**Answer:**
- contiguous U.S. stations only
- filtered using NOAA station metadata
- excludes Alaska, Hawaii, and territories

---

## 3. Modeling Questions

### Q5: Is wind modeling feasible from this dataset?

**Answer:**
Yes.

- `WND` provides:
  - wind speed
  - wind direction
  - quality control flags

This is sufficient to support:
- wind speed prediction
- wind energy estimation

---

### Q6: What is the modeling target?

**Answer:**
- primary target: **wind speed (m/s)**
- optionally transformed into wind energy potential

---

### Q7: What features will be used?

**Answer:**

Primary:
- wind speed (historical)

Secondary:
- temperature (`TMP`)
- dew point (`DEW`)
- pressure (`SLP`)
- optional: visibility (`VIS`), ceiling (`CIG`)

Derived:
- lag features (t-1, t-24)
- rolling statistics
- time-based features (hour, season)

---

### Q8: What is explicitly out of scope?

**Answer:**
- solar energy forecasting
- global station coverage
- sparse auxiliary encoded fields

---

## 4. Engineering Questions

### Q9: How do we handle large-scale data?

**Answer:**
- local development on small subsets
- distributed processing using PySpark on EC2
- S3 as primary storage layer

---

### Q10: How do we ensure reproducibility?

**Answer:**
- config-driven system (no hardcoding)
- user-specific configs for AWS resources
- consistent path resolution across environments

---

### Q11: What is the data pipeline structure?

**Answer:**

- ingestion → parsing → cleaning → storage (bronze/silver/gold)
- feature engineering → modeling → forecasting

---

## 5. Development Strategy Questions

### Q12: How do we develop locally?

**Answer:**
Use a small representative subset:

- ~150 stations
- years: 2018–2020
- states:
  - CA
  - TX
  - MN
  - FL

---

### Q13: How do we scale?

**Answer:**
- apply the same logic to:
  - all contiguous U.S. stations
  - full project time window
- run on Spark cluster (EC2)

---

## 6. Validation Questions

### Q14: How do we validate data quality?

**Answer:**
- apply QC flags
- remove sentinel values (e.g., 9999)
- validate numeric ranges
- inspect distributions

---

### Q15: How do we validate models?

**Answer:**
- train/test split (time-based)
- evaluation metrics (RMSE, MAE)
- compare multiple models

---

## 7. Final Framing

### What are we building?

A wind-focused data pipeline that:

- ingests NOAA ISD weather data
- parses encoded meteorological fields
- filters and cleans observations using QC rules
- joins station metadata for geographic context
- produces structured datasets for wind modeling

---

### Why this approach?

- NOAA ISD provides large-scale, real-world weather observations
- the `WND` field enables direct wind speed extraction
- a contiguous U.S. scope reduces noise while maintaining scale
- local-first development enables fast iteration before Spark scaling

---

### Key design choices

- wind is the primary modeling target
- auxiliary weather variables are secondary features
- sparse optional fields are excluded
- solar forecasting is out of scope