# Wind Energy Forecasting Pipeline

## 1. Problem Statement

Wind energy is a critical component of renewable energy systems, but its variability makes forecasting challenging. Accurate short-term wind forecasting is essential for grid stability, energy trading, and operational planning.

This project builds a scalable, end-to-end data pipeline to process large-scale meteorological data and generate wind energy forecasts across the United States.

---

## 2. Dataset — NOAA Integrated Surface Database (ISD)

- Source: NOAA ISD (AWS Open Data)
- Scale: ~600GB raw data
- Coverage:
  - ~35,000 global stations
  - Hourly observations
  - 1901–2025

For this project:
- Geographic scope: Contiguous U.S.
- Time window: 1995–2025

Key variables:
- Wind speed and direction (primary)
- Temperature, pressure, visibility (auxiliary)

---

## 3. System Architecture

The pipeline follows a modern data lake architecture:

```

Raw NOAA Data
→ Bronze (ingestion)
→ Silver (cleaned + parsed)
→ Gold (analytics + ML tables)
→ ML Models
→ Forecast Outputs

```

### Technologies

- PySpark (distributed processing)
- AWS S3 + EC2
- Apache Airflow (orchestration)
- DuckDB (benchmarking)
- Pandas / Matplotlib (visualization)

---

## 4. Data Processing (ETL)

### Bronze Layer
- Raw ingestion from NOAA S3
- Normalized schema
- Handles missing files

### Silver Layer
- Parsed encoded fields
- Unit standardization
- Quality control filtering
- Metadata enrichment

### Gold Layer
- Aggregated analytics tables
- ML-ready feature tables
- Time-based splits

---

## 5. Wind Energy Modeling

Wind potential is modeled using **capacity factor**, representing normalized energy output.

Key components:
- Turbine-inspired power curve
- Wind speed thresholds (cut-in, rated, cut-out)
- Spark-native implementation (no UDFs)

---

## 6. Machine Learning

### Models Tested
- Baseline
- Linear Regression
- Random Forest
- Gradient Boosted Trees (GBT)

### Final Model
- **Tuned GBT**

### Performance
- RMSE ≈ 0.042
- MAE ≈ 0.025

The model captures general trends but struggles with high-variance wind events.

---

## 7. Forecasting

- Batch inference pipeline
- Forecast horizon: 24–72 hours
- Stored in S3 for downstream use

### Forecast Performance
- RMSE ≈ 0.0455
- MAE ≈ 0.0275
- Bias ≈ ~0

---

## 8. Orchestration (Apache Airflow)

The pipeline is orchestrated using Airflow:

### DAG Tasks
- Bronze ingestion
- Silver processing
- Gold table generation
- Feature engineering
- Model training
- Forecast generation

Supports:
- Dry-run mode (safe execution)
- Full production runs

---

## 9. Benchmarking — DuckDB vs Spark

We compare:
- DuckDB (single-node)
- Spark (distributed)

### Key Findings

- DuckDB is faster for small datasets
- Spark has overhead but scales to large data
- Spark is necessary for full NOAA processing

---

## 10. Results & Visualizations

### Forecast vs Actual

![Forecast vs Actual](../../outputs/figures/forecast_vs_actual.png)

- Model captures trends
- Underestimates extreme spikes

---

### Regional Trends

![Regional Trends](../../outputs/figures/regional_wind_trends.png)

- TX shows strongest sustained wind potential
- MN shows high variability
- FL remains consistently low

---

### Seasonal Trends

![Seasonal Trends](../../outputs/figures/seasonal_trends.png)

- Peak wind in spring
- Lowest in summer
- Strong seasonal patterns across regions

---

### Benchmark Comparison

![Benchmark](../../outputs/figures/benchmark_comparison.png)

- DuckDB outperforms locally
- Spark required for scale

---

### U.S. Wind Potential Map

![Wind Map](../../outputs/figures/us_wind_potential_map.png)

- Strong wind regions in Midwest
- Lower wind potential in Southeast
- Clear geographic variation

---

## 11. Limitations

- Model struggles with extreme wind events
- No real-time streaming
- Limited feature set (no external weather models)
- Spatial resolution limited to station aggregation

---

## 12. Conclusion

This project demonstrates a full production-style pipeline:

- Scalable data processing (Spark)
- Structured data lake architecture
- ML-based forecasting system
- Airflow orchestration
- Cross-engine benchmarking

It highlights the trade-offs between local and distributed systems and provides a foundation for real-world renewable energy forecasting applications.

---

## 13. Future Work

- Real-time streaming forecasts
- Advanced deep learning models
- Integration with external weather APIs
- Deployment as an interactive dashboard
- Grid-level forecasting