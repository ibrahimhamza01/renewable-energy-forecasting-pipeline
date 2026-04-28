# Project Question Map

## Purpose

This document defines the final analytical story for the Wind Energy Forecasting Pipeline project.

Layer 7 locks the project questions, supporting Gold tables, chart sources, and forecasting target before feature engineering and machine learning. The goal is not to build the most complex model. The goal is to produce an interpretable, scalable, and insightful analysis of U.S. wind energy potential from 1995–2025.

---

## Final Project Story

This project asks:

> How has wind energy potential varied across the contiguous United States from 1995–2025, and what does that reveal about where wind is strongest, most seasonal, most stable, and most forecastable?

The project uses NOAA ISD hourly meteorological observations, Spark-based distributed processing, and physically informed wind power logic to transform raw weather records into interpretable wind potential indices.

The final analysis focuses on:

- spatial wind potential
- seasonal wind behavior
- long-run state-level differences
- stability and variability
- data quality and retention
- forecast readiness
- Spark vs DuckDB scalability tradeoffs

---

## Final Questions

| ID | Final Question | Why This Matters | Primary Table | Grain | Primary Metric |
|---|---|---|---|---|---|
| Q1 | Where is wind potential strongest in the contiguous U.S.? | Identifies the strongest long-run wind regions and supports the spatial story. | `gold/wind/region/monthly` | state-month | `monthly_region_capacity_factor` |
| Q2 | How does wind potential vary by season? | Shows whether wind follows interpretable seasonal patterns. | `gold/wind/region/monthly` | state-month | `monthly_region_capacity_factor`, `monthly_mean_wind_speed_ms` |
| Q3 | Which states have the most stable wind potential over time? | Separates consistently useful wind regions from highly variable ones. | `gold/wind/region/daily` and `gold/wind/region/monthly` | state-day / state-month | mean, standard deviation, coefficient of variation |
| Q4 | Which states are high-potential but unstable? | Adds critical thinking beyond ranking by average wind potential. | `gold/wind/region/daily` | state-day | average capacity factor, volatility, extreme-day frequency |
| Q5 | How much data is lost after quality control and Gold aggregation? | Explains trust, filtering, and data quality impact. | Bronze/Silver validation summaries + Gold validation outputs | pipeline stage | row counts, retention rate, valid output counts |
| Q6 | What time scale is most useful for interpretation: hourly, daily, or monthly? | Justifies why the project reports monthly trends but forecasts daily values. | `gold/wind/station/hourly`, `gold/wind/region/daily`, `gold/wind/region/monthly` | hour / day / month | interpretability, noise, stability |
| Q7 | Can next-day regional wind potential be forecast accurately? | Defines the ML task without letting ML dominate the project. | `gold/wind/region/daily` and future `gold_ml_base_wind` | state-day | next-day daily regional capacity factor |
| Q8 | When should Spark be used instead of DuckDB for this project? | Demonstrates big-data judgment and tool selection. | benchmark outputs | workload-level | runtime, memory behavior, scalability, usability |

---

## Confirmed Gold Tables

The following Gold tables are available and readable from S3:

| Table | Path | Grain | Rows | Use |
|---|---|---:|---:|---|
| Station hourly wind | `gold/wind/station/hourly` | station-hour | 812,991,212 | detailed wind power validation, hourly behavior |
| Station daily wind | `gold/wind/station/daily` | station-day | 19,430,672 | station-level daily aggregation |
| Region daily wind | `gold/wind/region/daily` | state-day | 537,449 | forecasting target, daily variability, stability |
| Region monthly wind | `gold/wind/region/monthly` | state-month | 17,664 | presentation, seasonal trends, long-run rankings |

---

## Validated Coverage

The Gold layer supports the full project scope:

| Check | Result |
|---|---:|
| Minimum year | 1995 |
| Maximum year | 2025 |
| Year count | 31 |
| State count | 48 contiguous U.S. states |
| Region daily rows | 537,449 |
| Region monthly rows | 17,664 |

The 2025 coverage is lower than prior full years because the year is incomplete.

---

## Validated Wind Index Ranges

| Metric | Minimum | Maximum | Result |
|---|---:|---:|---|
| Hourly normalized power | 0.0 | 1.0 | valid |
| Daily regional capacity factor | 0.0 | 0.900287 | valid |
| Monthly regional capacity factor | 0.001662 | 0.274203 | valid |

Invalid value checks:

| Check | Bad Rows |
|---|---:|
| Hourly normalized power outside `[0, 1]` | 0 |
| Daily regional capacity factor outside `[0, 1]` | 0 |
| Monthly regional capacity factor outside `[0, 1]` | 0 |

---

## Question-to-Chart Map

| Question | Chart / Output | Source Table | Notes |
|---|---|---|---|
| Q1 | Ranked bar chart of top and bottom states | `gold/wind/region/monthly` | Use long-run average monthly capacity factor |
| Q1 | U.S. state map of average wind potential | `gold/wind/region/monthly` | Presentation-friendly spatial view |
| Q2 | Monthly seasonal line chart | `gold/wind/region/monthly` | Average across states and years by month |
| Q2 | Seasonal comparison by selected states | `gold/wind/region/monthly` | Shows whether seasonality differs by region |
| Q3 | Stability ranking table | `gold/wind/region/daily` | Rank by coefficient of variation |
| Q4 | Potential vs variability scatter plot | `gold/wind/region/daily` | Identifies high-potential but unstable states |
| Q5 | Pipeline retention table | Bronze/Silver/Gold summaries | Shows data loss and QC effect |
| Q6 | Hourly vs daily vs monthly comparison table | Gold hourly/daily/monthly tables | Explains grain choice |
| Q7 | Actual vs predicted next-day capacity factor | `gold_ml_base_wind` | Later ML validation |
| Q8 | Spark vs DuckDB benchmark chart | benchmark outputs | Compare runtime and scalability by workload |

---

## Current Findings from Gold Validation

### Seasonal Pattern

Wind potential is highest in late winter and spring.

| Month | Average Monthly Capacity Factor | Average Wind Speed |
|---:|---:|---:|
| January | 0.051338 | 3.5350 |
| February | 0.054658 | 3.6452 |
| March | 0.060766 | 3.8397 |
| April | 0.063079 | 3.8994 |
| July | 0.023911 | 2.8263 |
| August | 0.021338 | 2.6783 |
| December | 0.047180 | 3.3723 |

Interpretation:

Wind potential rises in winter and spring, declines in summer, and begins rising again in fall and winter. This gives the project a strong descriptive insight before ML begins.

---

### Highest Long-Run Wind Potential States

| Rank Group | State | Average Monthly Capacity Factor | Average Wind Speed |
|---|---|---:|---:|
| High | ND | 0.092272 | 4.6982 |
| High | SD | 0.089094 | 4.5054 |
| High | KS | 0.083958 | 4.5597 |
| High | NE | 0.078505 | 4.3294 |
| High | MT | 0.078430 | 4.0629 |
| High | WY | 0.077021 | 3.9055 |
| High | IA | 0.065962 | 4.1542 |
| High | OK | 0.062456 | 3.9980 |
| High | TX | 0.055899 | 3.9152 |

Interpretation:

The strongest long-run wind potential is concentrated in the Great Plains and northern interior states. This matches expected U.S. wind geography and supports the physical plausibility of the Gold outputs.

---

### Lowest Long-Run Wind Potential States

| State | Average Monthly Capacity Factor | Average Wind Speed |
|---|---:|---:|
| GA | 0.013475 | 2.2820 |
| WV | 0.015278 | 2.2824 |
| AL | 0.016610 | 2.4683 |
| SC | 0.017603 | 2.5860 |
| TN | 0.017762 | 2.4740 |

Interpretation:

Lower wind potential is concentrated in the Southeast and Appalachian regions. This contrast strengthens the spatial story.

---

## Main Forecasting Target

The final ML target is:

```text
next_day_daily_region_capacity_factor
````

Defined as:

```text
target date = current date + 1 day
target grain = state-day
target source = gold/wind/region/daily
target column = daily_region_capacity_factor shifted one day ahead within each state
```

The modeling table will use:

```text
gold_ml_base_wind
```

Forecasting should remain secondary to the descriptive analysis. The model exists to answer whether recent wind behavior and seasonality can forecast next-day regional wind potential, not to dominate the project.

---

## Planned Final Analytical Tables

| Final Table                  | Grain                  | Purpose                                     | Status                                   |
| ---------------------------- | ---------------------- | ------------------------------------------- | ---------------------------------------- |
| `gold_daily_region_wind`     | state-day              | Daily analysis, stability, ML target        | build in Layer 7                         |
| `gold_monthly_state_wind`    | state-month            | Reporting, seasonality, long-run rankings   | build in Layer 7                         |
| `gold_extreme_event_windows` | state-day/event-window | Extreme high/low wind periods and stability | build in Layer 7 or later if time allows |
| `gold_ml_base_wind`          | state-day              | Forecast-ready model base table             | build in Layer 7/8                       |

---

## Spark vs DuckDB Question

Spark vs DuckDB should be treated as an analytical question:

> When does this project need distributed Spark, and when is single-node DuckDB enough?

This comparison should not only report speed. It should explain tool choice.

### Benchmark workloads

| Benchmark Task                     | Dataset                      | Spark Role                          | DuckDB Role                     |
| ---------------------------------- | ---------------------------- | ----------------------------------- | ------------------------------- |
| Filter by year and state           | Gold daily/monthly           | Tests partition pruning             | Tests local analytical speed    |
| Aggregate daily to monthly         | Gold daily                   | Tests distributed groupBy           | Tests single-node aggregation   |
| Rank states by wind potential      | Gold monthly                 | Tests scalable summary analytics    | Tests fast local reporting      |
| Compute seasonal trends            | Gold monthly                 | Tests distributed grouped summaries | Tests local EDA                 |
| Join station metadata              | Silver or station-level Gold | Tests distributed join behavior     | Tests local join feasibility    |
| Large-scale row count / validation | Bronze/Silver/Gold           | Best suited for Spark               | May be infeasible at full scale |

### Expected interpretation

DuckDB is likely best for:

* small exported subsets
* final reporting tables
* local EDA
* fast iteration
* presentation-ready summaries

Spark is necessary for:

* reading many NOAA station-year files
* Bronze and Silver creation
* large-scale parsing and QC
* full Gold generation
* station-hour and station-day workloads
* distributed joins and partitioned writes

Final conclusion should explain:

> DuckDB is excellent for local analytical iteration once Spark has reduced the raw data into compact Gold tables. Spark is required for the full-scale engineering pipeline because the raw NOAA ISD data and station-level Gold outputs are too large and fragmented for comfortable single-node processing.

---

## Layer 7 Validation Checklist

Before moving to feature engineering or ML, confirm:

* [x] Gold tables are readable from S3
* [x] Gold tables cover 1995–2025
* [x] Gold tables cover 48 contiguous U.S. states
* [x] Hourly normalized power is bounded between 0 and 1
* [x] Daily regional capacity factor is bounded between 0 and 1
* [x] Monthly regional capacity factor is bounded between 0 and 1
* [x] Seasonal pattern is physically plausible
* [x] Regional pattern is physically plausible
* [x] Main descriptive questions are fixed
* [x] Forecast target is fixed
* [ ] Final Layer 7 analytical tables are assembled
* [ ] Spark vs DuckDB benchmark plan is finalized
* [ ] Every final chart has a source table
* [ ] Every final question has a supporting table

---

## Final Layer 7 Decision

The project will prioritize interpretable descriptive analysis over model complexity.

The central deliverable is a coherent wind energy story:

1. where wind potential is strongest,
2. when wind potential is strongest,
3. which states are stable or volatile,
4. whether the Gold data is trustworthy,
5. whether daily regional wind potential can be forecast,
6. and why Spark is needed for scale while DuckDB remains useful for local analysis.

This question map is the contract for all downstream Layer 7, Layer 8, ML, benchmarking, visualization, and final presentation work.