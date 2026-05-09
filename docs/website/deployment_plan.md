# Website Deployment Plan

# Goal

Deploy the Live Wind Forecasting Platform as a public portfolio-grade product.

The deployed system should:

- work independently of EC2/S3
- support static analytical dashboards
- support live NOAA-powered wind estimation
- optionally support deployable ML inference
- remain inexpensive to host
- remain easy to maintain

---

# High-Level Architecture

```text
                NOAA Weather API
                        |
                        v
              +------------------+
              |   FastAPI API    |
              |  Model Service   |
              +------------------+
                        |
                        v
+------------------------------------------------+
|                Next.js Frontend                |
|                                                |
|  Static Assets + Charts + Live Estimation UI   |
+------------------------------------------------+
                        |
                        v
                 Public Website
````

---

# Frontend Architecture

## Framework

Next.js

Reasons:

* production-grade React framework
* strong TypeScript support
* easy deployment
* excellent SEO
* static + dynamic rendering support
* strong developer experience

---

## Frontend Responsibilities

The frontend handles:

* rendering pipeline dashboards
* displaying exported Spark artifacts
* rendering charts and maps
* fetching live NOAA observations
* displaying live wind estimates
* calling optional prediction API

---

## Frontend Hosting

Recommended:

```text
Vercel
```

Reasons:

* free tier sufficient
* optimized for Next.js
* automatic GitHub deployment
* preview deployments
* CDN support

---

# Backend Architecture

## Framework

FastAPI

Reasons:

* lightweight
* fast development
* async support
* easy ML serving
* automatic OpenAPI docs
* easy Docker deployment

---

## Backend Responsibilities

The backend handles:

* optional portable ML inference
* NOAA data fetching
* feature vector construction
* prediction serving
* model artifact loading
* API validation

---

## Backend Hosting

Recommended options:

### Render

Best balance of simplicity and reliability.

### Railway

Very easy deployment workflow.

### Fly.io

Excellent for container deployments.

---

# Model Architecture

## Original Training System

Original model training:

```text
Spark MLlib GBT
```

This remains the authoritative training workflow.

---

## Portable Deployment Model

Recommended deployment model:

```text
XGBoost Regressor
```

Reasons:

* portable
* easy inference
* no Spark dependency
* strong prediction performance
* simple JSON export

---

# Static Website Artifacts

The frontend should bundle all required static artifacts locally.

## Static assets

```text
website/public/assets/
```

Includes:

* maps
* trend figures
* benchmark plots
* Airflow screenshots
* architecture diagrams

---

## Static data

```text
website/public/data/
```

Includes:

* CSV exports
* JSON metrics
* benchmark outputs
* forecast outputs
* station metadata

---

# CI/CD Direction

## Frontend CI

GitHub Actions:

```text
.github/workflows/website_ci.yml
```

Tasks:

* install dependencies
* lint
* build
* deploy preview

---

## Backend CI

GitHub Actions:

```text
.github/workflows/model_service_ci.yml
```

Tasks:

* install dependencies
* run tests
* validate API
* build Docker image

---

# Environment Variables

## Frontend

```env
NEXT_PUBLIC_MODEL_API_URL=
```

---

## Backend

```env
NOAA_USER_AGENT=
MODEL_ARTIFACT_DIR=
CORS_ALLOWED_ORIGINS=
```

---

# Production Goals

The deployed website should:

* load quickly
* work on mobile
* support dark mode
* support live NOAA fetches
* degrade gracefully if APIs fail
* avoid large payloads
* remain usable without backend inference

---

# Non-Goals

The deployment does not attempt to:

* run Spark in production
* retrain models online
* process NOAA bulk data live
* reproduce the entire ETL pipeline in the browser

---

# Final Deployment Targets

## Frontend

```text
Vercel
```

## Backend

```text
Render or Railway
```

## Repository

```text
GitHub
```

---

# Success Criteria

Deployment is successful when:

* frontend is public
* backend is public
* static charts load correctly
* NOAA live estimation works
* optional prediction API works
* recruiter demo flow is smooth