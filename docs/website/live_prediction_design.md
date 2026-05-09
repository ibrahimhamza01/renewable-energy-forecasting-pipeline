# Live Prediction System Design

# Goal

Provide a live forecasting experience using current NOAA weather observations and project forecasting logic.

The live system should:

- demonstrate real-time interaction
- showcase forecasting concepts
- remain lightweight
- avoid Spark dependencies
- work after EC2/S3 expiration

---

# Core Design Principle

Separate:

- historical Spark processing
from
- lightweight live inference

The Spark pipeline generates historical datasets and model artifacts.

The live system consumes lightweight exported artifacts and NOAA API observations.

---

# Live System Modes

## Mode 1 — Physics-Based Estimation

This is the default live mode.

Uses:

- NOAA live observations
- turbine-inspired power curve
- current wind speed
- simple engineering logic

This mode requires no backend model service.

---

## Mode 2 — Portable ML Inference

Optional advanced mode.

Uses:

- exported feature defaults
- portable XGBoost model
- FastAPI inference service
- live NOAA observations

This mode allows deployed ML predictions without Spark.

---

# NOAA Data Source

## API

```text
https://api.weather.gov/
````

---

## Example Endpoint

```text
https://api.weather.gov/stations/KSFO/observations/latest
```

---

# Initial Supported Stations

## California

* KSFO

## Texas

* KIAH

## Minnesota

* KMSP

## Florida

* KMIA

These align with the original project development scope.

---

# Live Observation Fields

## Required NOAA fields

### Wind speed

```text
windSpeed.value
```

### Wind direction

```text
windDirection.value
```

### Temperature

```text
temperature.value
```

### Timestamp

```text
timestamp
```

---

# Physics-Based Power Curve

## Parameters

### Cut-in speed

```text
3 m/s
```

### Rated speed

```text
12 m/s
```

### Cut-out speed

```text
25 m/s
```

---

# Capacity Factor Logic

## Below cut-in

```text
0
```

## Between cut-in and rated

Scaled cubic output.

## Between rated and cut-out

```text
1.0
```

## Above cut-out

```text
0
```

---

# Frontend Live Flow

```text
User selects station
        |
        v
Frontend calls NOAA API
        |
        v
Observation parsed
        |
        v
Power curve evaluated
        |
        v
Capacity factor displayed
```

---

# Optional ML Inference Flow

```text
User selects station
        |
        v
Frontend fetches NOAA data
        |
        v
Frontend calls FastAPI backend
        |
        v
Backend builds feature vector
        |
        v
XGBoost predicts next-day capacity factor
        |
        v
Prediction returned to frontend
```

---

# Important Product Wording

Allowed wording:

```text
Live wind potential estimate using NOAA observations and power-curve logic.
```

Allowed wording if API deployed:

```text
Live prediction using a portable deployed ML model trained from pipeline-generated features.
```

---

# Disallowed Wording

Do not claim:

```text
Live Spark GBT forecast
```

unless Spark is actually deployed behind the inference API.

---

# Failure Handling

The website must gracefully handle:

* NOAA outages
* missing observations
* API throttling
* incomplete station data
* backend downtime

Fallback behavior:

* cached demo data
* last successful observation
* explanatory UI state

---

# Design Goals

The live prediction system should be:

* lightweight
* explainable
* visually impressive
* technically honest
* portfolio-friendly
* deployable at low cost

---

# Future Extensions

Possible future work:

* additional NOAA stations
* hourly forecasting
* animated wind maps
* WebSocket streaming
* battery/storage optimization
* grid demand overlays
* real-time feature stores
* retraining pipelines

---

# Success Criteria

The live system is successful when:

* live NOAA fetches work
* capacity factor estimates update correctly
* optional ML inference works
* UI remains responsive
* users understand what is live vs precomputed