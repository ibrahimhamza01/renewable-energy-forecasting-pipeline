# Final Handoff Checklist

## 1. Final Figures

Required figures:

- [ ] U.S. wind potential map
- [ ] Seasonal wind trend plot
- [ ] Multi-decade wind trend plot
- [ ] Forecast vs actual plot
- [ ] DuckDB vs Spark benchmark chart

Output folder:

```text
outputs/figures/
````

Expected files:

```text
outputs/figures/us_wind_potential_map.png
outputs/figures/seasonal_wind_trends.png
outputs/figures/multidecade_wind_trends.png
outputs/figures/forecast_vs_actual.png
outputs/figures/benchmark_comparison.png
```

---

## 2. Website/Dashboard Data

Required small exported files:

```text
website_data/forecasts/sample_forecasts.csv
website_data/actuals/forecast_vs_actual.csv
website_data/trends/regional_trends.csv
website_data/benchmarks/benchmark_comparison.csv
website_data/metrics/model_metrics.json
```

---

## 3. Final Written Deliverables

Required files:

```text
reports/final/final_report.md
docs/presentation/website_content.md
docs/presentation/outline.md
README.md
```

---

## 4. Reproducibility Checks

* [ ] `uv sync` works
* [ ] `source .venv/bin/activate` works
* [ ] `PROJECT_USER_CONFIG` is documented
* [ ] Local sample pipeline command is documented
* [ ] Benchmark command is documented
* [ ] Airflow dry-run command is documented
* [ ] Forecast output path is documented
* [ ] Figure export command is documented

---

## 5. Demo Flow

Presentation/demo order:

1. Show problem statement
2. Show architecture
3. Show Airflow DAG
4. Show wind potential maps
5. Show trend charts
6. Show forecast vs actual
7. Show benchmark comparison
8. Show limitations
9. Show reproducibility instructions
10. Conclude with final deliverables