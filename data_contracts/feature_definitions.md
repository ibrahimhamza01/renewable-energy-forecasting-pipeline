# Wind Forecasting Feature Definitions

## Overview

This document defines the full feature set used for wind energy forecasting.

The dataset is derived from NOAA ISD data and processed through the pipeline:

raw → parsed → cleaned → enriched → gold analytics → feature engineering

The resulting feature table is used for machine learning models that forecast
next-day regional wind potential.

---

## Dataset Grain

- **Primary entity:** state (U.S. state)
- **Temporal grain:** daily
- **Row definition:** one row per (state, date)

---

## Core Columns

### Date Column
- `date_utc`
  - Type: date
  - Description: canonical timestamp used for all temporal logic

### Entity Column
- `state`
  - Type: string
  - Description: U.S. state identifier

---

## Target Definition

- `next_day_daily_region_capacity_factor`
  - Type: float
  - Range: [0, 1]
  - Description:
    Wind capacity factor for the next day (t+1)

- `daily_region_capacity_factor`
  - Type: float
  - Description:
    Same-day capacity factor (used only for feature generation)

---

## Temporal Features

These features are deterministic and known at prediction time.

- `year`
- `month`
- `day_of_year`
- `day_of_month`
- `day_of_week`
- `is_weekend` (boolean)
- `season` (categorical: winter, spring, summer, fall)

---

## Lag Features

Lag features capture historical wind behavior.

All lag features are strictly **past values only**.

Examples:

- `daily_region_capacity_factor_lag_1d`
- `daily_region_capacity_factor_lag_2d`
- `daily_region_capacity_factor_lag_3d`
- `daily_region_capacity_factor_lag_7d`
- `daily_region_capacity_factor_lag_14d`
- `daily_region_capacity_factor_lag_30d`

---

## Lag Delta Features

These capture short-term vs long-term change signals.

Examples:

- `lag_1d - lag_7d`
- `lag_1d - lag_14d`
- `lag_1d - lag_30d`

---

## Rolling Features

Rolling features summarize recent history.

All rolling windows exclude the current day to prevent leakage.

Examples:

- `daily_region_capacity_factor_rolling_3d_mean`
- `daily_region_capacity_factor_rolling_3d_min`
- `daily_region_capacity_factor_rolling_3d_max`
- `daily_region_capacity_factor_rolling_3d_stddev`

- `daily_region_capacity_factor_rolling_7d_mean`
- `daily_region_capacity_factor_rolling_14d_mean`
- `daily_region_capacity_factor_rolling_30d_mean`

---

## Additional Weather Features

Derived from regional aggregation:

- `mean_region_wind_speed_ms`
- `avg_station_wind_speed_std_ms`
- `daily_wind_speed_range_ms`
- `station_count`
- `total_hourly_observations`

---

## Split Definition

Time-based splits are used to prevent leakage.

- **Train:**
  - date ≤ 2019-12-31

- **Validation:**
  - 2020-01-01 ≤ date ≤ 2022-12-31

- **Test:**
  - date ≥ 2023-01-01

Column:
- `split` ∈ {train, validation, test}

---

## Leakage Rules

Strict anti-leakage guarantees:

1. No feature uses current or future target values
2. All lag features use only past observations
3. Rolling windows exclude the current row
4. Temporal features are deterministic (calendar-based)
5. Splits are purely time-based (no random sampling)

---

## Null Handling

- Lag and rolling features produce nulls at series boundaries
- Observed null count:
  - ~1 row per state for lag/rolling initialization
- No nulls in:
  - target column
  - date column
  - entity column

---

## Data Quality Guarantees

- Capacity factor values are within physical bounds [0, 1]
- No missing target values
- Partitioning ensures state-level independence
- Feature distributions are stable across splits

---

## Final Notes

This feature set is:

- Physically grounded (wind modeling)
- Temporally consistent (no leakage)
- Scalable (Spark-native transformations)
- Model-ready (structured for ML pipelines)

It serves as the canonical input to model training.