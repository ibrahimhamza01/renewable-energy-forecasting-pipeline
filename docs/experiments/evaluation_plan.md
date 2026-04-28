# Evaluation Plan — Wind Energy Forecasting Pipeline

## Purpose

This document defines how model performance will be evaluated and interpreted.

The goal is not only to measure prediction accuracy, but to:

- assess whether the model provides meaningful insight
- evaluate performance across space and time
- understand when and where the model works or fails
- connect model results back to the project’s analytical questions

This evaluation framework ensures that modeling supports interpretation and storytelling.

---

## Evaluation Philosophy

Evaluation is guided by the principle:

> A useful model is one that improves understanding, not just accuracy.

The model will be evaluated along three dimensions:

1. **Accuracy** — how close predictions are to actual values  
2. **Stability** — how performance varies across time and regions  
3. **Interpretability** — whether results can be explained and trusted  

---

## Forecasting Task

The evaluation focuses on:

```text
next_day_daily_region_capacity_factor
````

* Grain: state-day
* Source: `gold/wind/region/daily`
* Task: predict value at time t+1 using information at time t

---

## Baseline Comparison

All models must be compared to a simple baseline:

```text
prediction(t+1) = value(t)
```

### Why this matters

* wind patterns exhibit persistence
* a strong baseline is expected
* model must demonstrate real improvement

### Required outcome

> The model must outperform the baseline to be considered useful.

---

## Core Metrics

### 1. RMSE (Root Mean Squared Error)

* penalizes large errors
* useful for identifying extreme failures

---

### 2. MAE (Mean Absolute Error)

* interpretable average error
* less sensitive to outliers

---

## Evaluation Dimensions

### 1. Overall Performance

Evaluate:

* RMSE (global)
* MAE (global)

Purpose:

* establish baseline model quality

---

### 2. Performance by State

Evaluate:

* RMSE per state
* MAE per state

Purpose:

* identify geographic strengths and weaknesses
* connect to spatial wind patterns

Expected insight:

* high-wind regions may be easier to predict
* low-wind or volatile regions may show higher error

---

### 3. Performance by Season

Evaluate:

* RMSE by month or season
* MAE by month or season

Purpose:

* validate whether model captures seasonal patterns

Expected insight:

* winter/spring (higher wind) → potentially better predictability
* summer (low wind) → noisier behavior

---

### 4. Performance by Stability (Key Insight)

States will be grouped by variability:

* low variance (stable)
* medium variance
* high variance (volatile)

Evaluate:

* error vs variance relationship

Purpose:

* determine whether volatility drives prediction difficulty

This directly supports the question:

> Which regions are stable vs unstable?

---

## Extreme Event Evaluation

The model will be evaluated on extreme wind conditions.

### Define extremes

* low wind: bottom percentile of capacity factor
* high wind: top percentile of capacity factor

### Evaluate:

* error on extreme low days
* error on extreme high days

Purpose:

* assess model robustness
* evaluate behavior during rare but important conditions

This aligns with the proposal objective of:

> evaluating the impact of extreme weather on renewable energy stability 

---

## Distribution Checks

Predictions must be physically valid.

### Check:

* predicted values within [0, 1]
* no unrealistic spikes or negative values

Purpose:

* ensure consistency with wind capacity factor definition

---

## Residual Analysis

Analyze prediction errors:

* residual distribution
* bias (systematic over/under prediction)
* error vs actual value

Purpose:

* identify structural weaknesses in the model
* detect bias in specific ranges (e.g., low-wind vs high-wind)

---

## Temporal Stability

Evaluate performance across time:

* error by year
* error trend over time

Purpose:

* detect degradation or improvement over decades
* identify sensitivity to dataset coverage changes

---

## Comparison Across Models

All candidate models will be compared:

* Linear Regression
* Random Forest
* Gradient Boosted Trees

Evaluation criteria:

* RMSE / MAE
* stability across states
* robustness to extreme events
* interpretability

The final model will be selected based on:

> balanced performance + interpretability (not just lowest error)

---

## Spark vs DuckDB Evaluation

This project includes a system-level comparison.

### Evaluate:

* training time
* data loading time
* aggregation performance
* scalability

### Expected findings

DuckDB:

* faster for small datasets
* ideal for local experimentation
* efficient for EDA

Spark:

* required for full dataset
* scalable for ETL and training
* handles distributed workloads

This aligns with the proposal goal of:

> benchmarking distributed vs single-node systems 

---

## Success Criteria

The modeling approach is successful if:

1. Model outperforms baseline
2. Performance is stable across states and seasons
3. Errors are interpretable and explainable
4. Extreme events are handled reasonably
5. Predictions remain within valid physical bounds
6. Results support the project’s analytical questions

---

## Link to Project Questions

| Question                      | Evaluation Component                           |
| ----------------------------- | ---------------------------------------------- |
| Where is wind strongest?      | state-level performance + descriptive analysis |
| How does wind vary by season? | seasonal error analysis                        |
| Which regions are stable?     | error vs variance                              |
| Which are unstable?           | extreme event + variability analysis           |
| Is the data reliable?         | distribution + residual checks                 |
| Can wind be forecast?         | baseline vs model comparison                   |
| When to use Spark vs DuckDB?  | benchmark results                              |

---

## Final Statement

This evaluation plan ensures that modeling results:

* are not judged only by accuracy
* are interpreted in context
* contribute directly to understanding wind energy patterns

The final outcome is not just a model.

It is a **validated, interpretable explanation of wind energy behavior and predictability in the United States.**