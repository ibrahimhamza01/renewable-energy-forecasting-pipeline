# Wind Model Service

Portable FastAPI backend for live wind outlook analysis.

## Run locally

```bash
export FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
uvicorn model_service.app.main:app --reload --port 8000
```

## API docs

```text
http://127.0.0.1:8000/docs
```

## Endpoints

```text
GET  /health
GET  /metrics
GET  /stations
POST /analyze-live
```

## Required environment variables

```bash
FRONTEND_ORIGINS=https://your-vercel-app.vercel.app
NOAA_USER_AGENT=wind-energy-forecasting-platform/1.0 your-email@example.com
```

## Deployment target

Recommended free deployment:

```text
Render Web Service
```