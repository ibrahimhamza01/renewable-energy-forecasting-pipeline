# Website Data Export Audit

## Goal

This document tracks which exported website artifacts are:

- production-quality
- partial/demo subsets
- temporary placeholders
- requiring regeneration from Spark gold tables

The purpose is to ensure the final website only presents validated and representative outputs.

---

# Current Website Artifacts

## forecast_vs_actual.csv

Location:

```text
website/public/data/forecast_vs_actual.csv
```

Current status:

- schema valid
- readable
- likely subset/sample export
- currently contains:
  - 300 rows
  - region = TX only

Columns:

- date
- region
- actual
- predicted

Decision:

- usable temporarily
- should later be regenerated using:
  - broader regional coverage
  - larger test horizon
  - final production prediction export

---

## regional_trends.csv

Location:

```text
website/public/data/regional_trends.csv
```

Current status:

- schema valid
- readable
- likely reduced subset
- contains:
  - CA
  - TX
  - MN
  - FL

Columns:

- date
- region
- capacity_factor

Decision:

- acceptable for MVP website
- may later be regenerated with:
  - more states
  - longer aggregates
  - smoothed monthly trends

---

## seasonal_trends.csv

Location:

```text
website/public/data/seasonal_trends.csv
```

Current status:

- validated
- complete for current scoped states
- suitable for production website

Columns:

- region
- season
- capacity_factor

Decision:

- approved for website use

---

## us_wind_station_map.csv

Location:

```text
website/public/data/us_wind_station_map.csv
```

Current status:

- validated
- 2419 stations
- suitable for map visualizations

Columns:

- station_id
- latitude
- longitude
- state
- avg_wind_speed_ms

Decision:

- approved for website use

---

## model_metrics.json

Location:

```text
website/public/data/model_metrics.json
```

Current status:

- validated
- exported from final GBT evaluation metrics

Decision:

- approved for website use

---

## feature_importance.json

Location:

```text
website/public/data/feature_importance.json
```

Current status:

- validated
- exported from final tuned GBT model

Decision:

- approved for website use

---

## live_station_list.json

Location:

```text
website/public/data/live_station_list.json
```

Current status:

- manually configured
- temporary curated station set

Decision:

- later replace with dynamically generated station metadata export

---

# Planned Future Regenerations

The following artifacts may later be regenerated from Spark gold tables:

- forecast_vs_actual.csv
- regional_trends.csv
- benchmark_comparison.csv
- monthly_state_trends.csv
- gbt_predictions.json

These are not blockers for website development.

---

# Website Development Rule

Frontend development should proceed using current validated artifacts.

Artifacts can later be swapped with richer exports without changing frontend architecture.