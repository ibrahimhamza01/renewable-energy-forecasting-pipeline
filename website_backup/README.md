# Wind Forecasting Website

Frontend application for the Live Wind Forecasting Platform.

This website presents:

- distributed Spark pipeline outputs
- historical wind analytics
- forecasting model results
- benchmarking results
- live NOAA-powered wind estimation
- optional deployed ML inference

The website is designed to function independently of EC2/S3 infrastructure after artifact export.

---

# Frontend Stack

## Core Framework

- Next.js
- React
- TypeScript

## Visualization

- Plotly
- Recharts
- D3.js
- Leaflet / Mapbox (optional)

## Styling

- Tailwind CSS
- Framer Motion

## Deployment

- Vercel

---

# Planned Website Sections

## 1. Overview

Landing page describing:

- project goals
- NOAA ISD dataset
- Spark/Airflow architecture
- major technical achievements

---

## 2. Live Wind Explorer

Interactive NOAA-powered live estimator.

Features:

- station selector
- current weather observations
- live wind potential estimate
- power curve visualization
- fallback mode

---

## 3. Pipeline Architecture

Detailed engineering walkthrough.

Includes:

- Bronze/Silver/Gold architecture
- Airflow orchestration
- Spark processing
- ML training workflow
- benchmarking design

---

## 4. Wind Potential Results

Historical analytics dashboard.

Includes:

- U.S. wind potential maps
- regional trends
- seasonal patterns
- station-level analysis

---

## 5. Forecasting Model

Machine learning results dashboard.

Includes:

- model metrics
- forecast vs actual
- feature importance
- sample predictions

---

## 6. Benchmarking

DuckDB vs Spark comparison dashboard.

Includes:

- runtime comparisons
- scalability interpretation
- distributed vs local tradeoffs

---

## 7. Final Takeaways

Portfolio-style conclusions and engineering lessons.

---

# Local Development

## Install dependencies

```bash
npm install
````

## Start development server

```bash
npm run dev
```

## Production build

```bash
npm run build
```

---

# Planned Data Sources

## Static data

Loaded from:

```text
website/public/data/
website/public/assets/
```

## Live data

Fetched from:

```text
https://api.weather.gov/
```

## Optional backend API

Portable ML inference service:

```text
FastAPI + XGBoost
```

---

# Deployment Targets

## Frontend

* Vercel

## Backend

* Render
* Railway
* Fly.io

---

# Product Positioning

This website is intended to demonstrate:

* distributed data engineering
* cloud-based ETL
* production-style orchestration
* machine learning deployment
* analytical storytelling
* interactive forecasting interfaces

for portfolio and recruiting purposes.