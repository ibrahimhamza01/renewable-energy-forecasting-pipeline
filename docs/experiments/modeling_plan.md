# Modeling Plan — Wind Energy Forecasting Pipeline

## Purpose

This document defines the modeling strategy for the wind energy forecasting pipeline.

The goal is not to build the most complex model. The goal is to:

- produce interpretable insights about U.S. wind potential
- define a clear and meaningful forecasting target
- ensure modeling aligns with the data pipeline and physical logic
- avoid leakage and unrealistic assumptions
- support reproducibility and scalability

This document locks all modeling decisions before feature engineering and training begin.

---

## Project Framing

This project is primarily an **analytical and storytelling project**, supported by modeling.

The key objective is to understand:

> How wind energy potential varies across space and time in the U.S., and whether it can be forecast using recent observations and seasonal patterns.

Modeling is used as a tool to answer:

> Can next-day regional wind potential be predicted in a stable and interpretable way?

---

## Final Descriptive Questions

The modeling work supports the following core questions:

1. Where is wind potential strongest in the U.S.?
2. How does wind potential vary by season?
3. Which states have stable vs volatile wind behavior?
4. Which states are high-potential but unstable?
5. How reliable is the dataset after quality filtering?
6. What time resolution is most useful for analysis?
7. Can next-day regional wind potential be forecast?
8. When should Spark be used instead of DuckDB?

---

## Dependency on Gold Tables

All modeling is built on validated Gold tables produced in Layer 6:

- `gold/wind/region/daily` → primary modeling source
- `gold/wind/region/monthly` → descriptive analysis

These tables have been validated for:

- physical plausibility
- correct value ranges
- full coverage across 1995–2025
- complete state representation (48 contiguous U.S. states)

---

## Final Modeling Target

### Target Definition

```text
target = next_day_daily_region_capacity_factor
````

### Description

* Represents **regional wind energy potential at the daily level**
* Derived from physically informed wind power modeling
* Aggregated across all stations within a state
* Normalized between 0 and 1 (capacity factor)

### Grain

```text
state-day
```

### Source Table

```text
gold/wind/region/daily
```

### Target Construction

```text
target(t) = daily_region_capacity_factor at date t+1
```

Implemented using a time shift within each state.

---

## Why This Target?

### 1. Interpretability

* Capacity factor is widely understood in energy systems
* Values bounded between 0 and 1
* Directly reflects usable wind energy

### 2. Stability

* Daily aggregation reduces noise vs hourly data
* More suitable for storytelling and visualization

### 3. Forecast Relevance

* Next-day prediction aligns with real-world energy planning

### 4. Data Availability

* Fully supported by validated Gold tables
* No missing states or structural gaps

---

## Modeling Scope

The modeling task is:

> Predict next-day regional wind capacity factor using only past and present information.

This is a **supervised regression problem**.

---

## Feature Categories (Planned)

### 1. Temporal Features

* day of week
* month
* day of year
* seasonal indicators

Purpose:

* capture strong seasonal wind patterns observed in EDA

---

### 2. Lag Features

* previous day capacity factor
* lag values (1–7 days)

Purpose:

* capture short-term persistence in wind behavior

---

### 3. Rolling Features

* rolling mean (3-day, 7-day)
* rolling standard deviation
* rolling min/max

Purpose:

* capture trend and volatility

---

### 4. Regional Features

* state identifier
* long-run average wind potential (optional, time-aware)

Purpose:

* capture geographic differences

---

## Stability and Variability Modeling

The project does not only model average behavior, but also variability.

Key insights:

* stable states → easier to predict
* volatile states → harder to predict

Model evaluation will explicitly consider:

* error vs variance relationships
* performance differences across regions
* ability to handle high-variability periods

---

## Extreme Event Consideration

The project explicitly considers extreme wind conditions.

Extreme events include:

* very low wind days (near-zero capacity factor)
* very high wind days (upper percentile of capacity factor)

Why this matters:

* impacts grid reliability
* affects predictability
* differentiates stable vs unstable regions

Potential modeling signals:

* rolling min/max features
* deviation from rolling averages
* frequency of extreme days

---

## Explicitly Disallowed Features (Leakage Prevention)

Not allowed:

* future values of any variable
* features using target(t+1)
* same-day aggregates including future hours
* full-month aggregates for daily prediction
* global statistics computed across full dataset without time awareness

Key rule:

> At time t, only information available at or before t may be used.

---

## Data Splitting Strategy

Time-based split:

* Train: 1995–2015
* Validation: 2016–2020
* Test: 2021–2025

Why:

* preserves temporal structure
* avoids leakage
* reflects real forecasting setup

---

## Baseline Model

```text
prediction(t+1) = value(t)
```

Purpose:

* establish minimum performance
* measure added value of ML

---

## Candidate Models

### 1. Linear Regression

* interpretable
* baseline relationships

### 2. Random Forest

* handles non-linearity
* robust

### 3. Gradient Boosted Trees

* stronger performance
* still interpretable

No deep learning or overly complex models are required.

---

## Evaluation Metrics

Primary:

* RMSE
* MAE

Secondary:

* error by season
* error by state
* stability of predictions
* comparison to baseline

---

## Success Criteria

A model is successful if:

1. Outperforms persistence baseline
2. Stable performance across seasons
3. Consistent across states
4. Predictions remain within [0, 1]
5. Results are interpretable

---

## Relationship to EDA

Observed patterns → modeling decisions:

* strong seasonality → temporal features
* regional differences → state features
* variability → rolling std features
* noisy hourly data → daily target

---

## Role of Spark vs DuckDB in Modeling

### Spark is required for:

* large-scale feature table generation
* distributed model training
* full dataset processing (1995–2025)

### DuckDB is useful for:

* local experimentation
* fast EDA
* feature validation
* small-sample modeling

### Comparison Goals

The project will evaluate:

* runtime differences
* data loading cost
* scalability
* usability

Conclusion:

> Spark is necessary for large-scale pipeline execution, while DuckDB is ideal for local analytical iteration and validation.

---

## What This Project Does NOT Aim To Do

This project does not aim to:

* build the most complex model
* maximize predictive accuracy at all costs
* use black-box deep learning
* perform long-horizon forecasting
* heavily tune hyperparameters

Instead, the focus is on:

* interpretability
* physical realism
* reproducibility
* scalable design

---

## Final Statement

This modeling plan prioritizes:

* interpretability over complexity
* physically grounded targets
* realistic forecasting setup
* strict leakage prevention
* alignment with analytical storytelling

The model is not the goal.

The goal is to:

> understand, explain, and responsibly forecast wind energy potential at scale.