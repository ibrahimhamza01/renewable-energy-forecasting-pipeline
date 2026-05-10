# Live Prediction System Design

# Goal

Provide a deployable live wind analysis experience using current NOAA weather observations, preserved Spark pipeline artifacts, and lightweight backend inference logic.

The live system should:

- demonstrate real-time interaction
- showcase forecasting and energy-analysis concepts
- remain lightweight
- avoid Spark runtime dependencies
- work after EC2/S3 expiration
- support deployable backend APIs
- remain technically honest about live inference capabilities

---

# Core Design Principle

Separate:

- historical distributed Spark processing

from

- lightweight deployable live analysis services

The Spark pipeline generates:

- historical datasets
- forecasting evaluations
- benchmark outputs
- model metrics
- station metadata
- analytical artifacts

The live system consumes:

- preserved frontend-safe artifacts
- NOAA/NWS live observations
- portable backend logic
- turbine-inspired wind estimation

without requiring a running Spark cluster.

---

# Current Live System Architecture

The deployed live system combines:

```text
NOAA/NWS live observations
+
frontend station explorer
+
power-curve wind estimation
+
portable FastAPI backend
+
historical Spark artifact context
```

The backend service does not retrain or serve the Spark MLlib GBT model.

Instead, it provides:

- live wind analysis
- historical contextualization
- heuristic next-24-hour outlook estimation
- portable deployable backend infrastructure

---

# Current Live System Modes

## Mode 1 — Frontend Physics-Based Estimation

Implemented in the Next.js frontend.

Uses:

- NOAA live observations
- turbine-inspired power curve
- current wind speed
- browser-side estimation logic

This mode requires no backend service.

Implemented route:

```text
/live
```

Implemented files:

```text
website/src/lib/noaaClient.ts
website/src/lib/powerCurve.ts
website/src/lib/stationData.ts
website/src/components/LiveWindExplorer.tsx
website/src/components/PowerCurveChart.tsx
website/src/app/live/page.tsx
```

---

## Mode 2 — Portable Live Analysis Backend

Implemented using FastAPI.

Uses:

- NOAA live observations
- preserved pipeline artifacts
- state-level historical summaries
- power-curve estimation
- heuristic outlook logic
- portable backend APIs

This mode provides:

- deployable backend infrastructure
- live outlook contextualization
- next-24-hour tendency estimation
- historical comparison summaries

without requiring Spark model serving.

Implemented backend files:

```text
model_service/app/main.py
model_service/app/live_analyzer.py
model_service/app/noaa_client.py
model_service/app/artifact_loader.py
```

---

# NOAA Data Source

## API

```text
https://api.weather.gov/
```

---

## Example Endpoint

```text
https://api.weather.gov/stations/KSFO/observations/latest
```

---

# Supported Live Station Universe

The live system uses:

```text
website/public/data/verified_live_station_list.json
```

Current verified coverage:

| Artifact | Count |
|---|---|
| verified live NOAA stations | 1,981 |
| state coverage | 48 states |

The frontend and backend only allow verified stations from the preserved pipeline exports.

---

# Live Observation Fields

## Required NOAA Fields

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

Interpretation:

```text
insufficient wind for turbine generation
```

---

## Between cut-in and rated

Uses cubic ramp-up estimation.

Interpretation:

```text
partial turbine output region
```

---

## Between rated and cut-out

```text
1.0
```

Interpretation:

```text
near-rated turbine output
```

---

## Above cut-out

```text
0
```

Interpretation:

```text
turbine protection shutdown region
```

---

# Frontend Live Flow

```text
User selects verified station
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
Estimated capacity factor displayed
        |
        v
Operating region visualized
```

---

# Portable Backend Live Flow

```text
User selects verified station
        |
        v
Frontend calls FastAPI backend
        |
        v
Backend validates station
        |
        v
Backend fetches NOAA observation
        |
        v
Live wind converted into estimated capacity factor
        |
        v
Historical state summaries loaded
        |
        v
Current conditions contextualized
        |
        v
Next-24-hour outlook estimated
        |
        v
JSON response returned to frontend
```

---

# Backend Analysis Outputs

The backend currently returns:

## Live observation summary

Includes:

- wind speed
- wind direction
- temperature
- observation age
- timestamp

---

## Current estimated capacity factor

Derived from:

```text
turbine-inspired power curve estimation
```

---

## Historical contextualization

Derived from preserved Spark artifacts:

```text
website/public/data/state_wind_summary.csv
website/public/data/model_metrics.json
```

Includes:

- long-run state capacity factor averages
- long-run state wind speed averages
- relative wind condition labels
- summary interpretation text

---

## Next-24-hour outlook

Provides:

- estimated outlook range
- center estimate
- tendency classification
- confidence label

This outlook is heuristic and artifact-based.

It is not generated by serving the Spark MLlib GBT model.

---

# Portable Backend API

## Local Development

Run backend:

```bash
uvicorn model_service.app.main:app --reload --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Example Endpoint

```text
POST /analyze-live
```

Example request:

```json
{
  "station_id": "KMSP"
}
```

---

# Historical Artifact Dependencies

The portable backend currently depends on preserved artifacts:

```text
website/public/data/state_wind_summary.csv
website/public/data/model_metrics.json
website/public/data/verified_live_station_list.json
```

These artifacts allow the backend to remain deployable without:

- Spark runtime
- EC2
- S3
- distributed inference infrastructure

---

# Important Product Wording

Allowed wording:

```text
Live wind outlook using NOAA observations, turbine-inspired power-curve logic, and preserved Spark pipeline artifacts.
```

Allowed wording:

```text
Deployable portable backend analysis service.
```

Allowed wording:

```text
Historical model metrics contextualize the live outlook.
```

---

# Disallowed Wording

Do not claim:

```text
Live Spark GBT forecast
```

Do not claim:

```text
Real-time ML inference from the trained Spark model
```

unless the Spark model is actually deployed behind a serving infrastructure.

---

# Failure Handling

The frontend and backend gracefully handle:

- NOAA outages
- unsupported station IDs
- missing observations
- API throttling
- malformed NOAA payloads
- backend downtime
- CORS configuration issues

Fallback behavior includes:

- validation errors
- explanatory UI states
- request failure messages
- station verification checks

---

# Design Goals

The live analysis platform should be:

- lightweight
- explainable
- visually impressive
- technically honest
- deployable
- low-cost
- portfolio-friendly
- infrastructure-independent

---

# Tradeoff Decision

The project intentionally does not retrain or convert the Spark MLlib GBT model into a portable XGBoost model.

Reasoning:

- the historical forecasting system already demonstrates full ML training workflows
- live feature generation for the Spark model would require unavailable rolling state
- serving Spark models would significantly increase deployment complexity
- portable heuristic analysis better matches low-cost portfolio deployment goals

The implemented solution prioritizes:

```text
deployability
+
technical honesty
+
live interactivity
+
artifact preservation
```

over real-time distributed model serving.

---

# Future Extensions

Possible future work:

- portable XGBoost retraining
- ONNX model export
- real deployed ML inference
- future weather forecast ingestion
- hourly forecasting
- animated wind maps
- WebSocket streaming
- battery/storage optimization
- grid demand overlays
- real-time feature stores
- scheduled retraining pipelines
- model drift monitoring

---

# Success Criteria

The live system is successful when:

- live NOAA fetches work
- backend APIs respond correctly
- verified station validation works
- capacity factor estimates update correctly
- live outlook summaries remain interpretable
- frontend remains responsive
- users understand what is live vs historical
- the platform remains deployable without Spark infrastructure