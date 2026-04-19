# S3 Layout

This document defines the config-driven S3 layout used by the
renewable-energy-forecasting-pipeline project.

The purpose of this layout is to ensure that:

- each teammate can use their own S3 bucket
- no code assumes one shared cloud bucket
- all S3 paths are resolved through config
- business logic never hardcodes bucket names or S3 prefixes

---

## 1. Bucket model

This project uses two categories of S3 storage.

### 1.1 Source bucket

The raw NOAA ISD dataset is read directly from the public AWS Open Data bucket:

```bash
s3://noaa-global-hourly-pds/
````

This bucket is external to the project and is treated as read-only.

### 1.2 Project bucket

Each teammate uses their own project bucket for all generated artifacts.

Example:

```bash
s3://syed-datsbd-s2026/
```

All project-managed outputs are written into this bucket using config-driven logical prefixes.

---

## 2. Path resolution model

S3 paths are resolved in two layers:

### 2.1 Logical paths

Defined in:

```bash
configs/paths.yaml
```

Example:

```yaml
bronze:
  isd: "bronze/isd"
```

### 2.2 User-specific bucket config

Defined in:

```bash
configs/users/<name>.yaml
```

Example:

```yaml
aws:
  source_bucket: noaa-global-hourly-pds
  project_bucket: syed-datsbd-s2026
```

### 2.3 Runtime resolution

The project resolves final S3 URIs through:

```bash
src/common/paths.py
```

Examples:

* `paths.raw_isd`
* `paths.bronze_isd`
* `paths.silver_weather`
* `paths.gold_wind_region_daily`

No bucket names should appear directly inside ETL or modeling code.

---

## 3. Source data layout

The public NOAA source bucket uses this layout pattern:

```bash
s3://noaa-global-hourly-pds/<year>/<station>.csv
```

Examples:

```bash
s3://noaa-global-hourly-pds/1901/02907099999.csv
s3://noaa-global-hourly-pds/1902/02950099999.csv
```

This project treats that bucket as the raw external source of truth.

Logical path:

```bash
paths.raw_isd
```

---

## 4. Project bucket layout

All generated project data is written under the active user's project bucket.

### 4.1 Bronze layer

Raw-to-internal storage layer.

Logical path:

```bash
paths.bronze_isd
```

Physical pattern:

```bash
s3://<project-bucket>/bronze/isd/
```

### 4.2 Silver layer

Parsed, cleaned, enriched weather data.

Logical path:

```bash
paths.silver_weather
```

Physical pattern:

```bash
s3://<project-bucket>/silver/weather/
```

### 4.3 Gold layer

Wind analytics and modeling tables.

Logical paths:

* `paths.gold_wind_station_hourly`
* `paths.gold_wind_station_daily`
* `paths.gold_wind_region_daily`
* `paths.gold_wind_region_monthly`

Physical patterns:

```bash
s3://<project-bucket>/gold/wind/station/hourly/
s3://<project-bucket>/gold/wind/station/daily/
s3://<project-bucket>/gold/wind/region/daily/
s3://<project-bucket>/gold/wind/region/monthly/
```

### 4.4 Model registry

Stores trained model artifacts and metadata.

Logical path:

```bash
paths.model_registry
```

Physical pattern:

```bash
s3://<project-bucket>/models/registry/
```

### 4.5 Forecast outputs

Stores prediction outputs.

Logical path:

```bash
paths.forecast_outputs
```

Physical pattern:

```bash
s3://<project-bucket>/forecasts/outputs/
```

### 4.6 Benchmark results

Stores benchmarking outputs and performance artifacts.

Logical path:

```bash
paths.benchmark_results
```

Physical pattern:

```bash
s3://<project-bucket>/benchmarks/results/
```

---

## 5. Design rules

### Rule 1 — no hardcoded bucket names

Do not write code like:

```python
"s3://syed-datsbd-s2026/bronze/isd"
```

Bucket selection must always come from config.

### Rule 2 — no inline S3 prefixes in business logic

Do not manually assemble storage prefixes inside ETL, ML, or reporting code.

Use:

* `src/common/paths.py`
* `src/common/aws_utils.py`

### Rule 3 — source and project buckets must remain separate

The NOAA public source bucket is not the same as the user's output bucket.

This separation prevents accidental coupling between source ingestion and project storage.

### Rule 4 — logical path names are the contract

`configs/paths.yaml` defines the logical storage contract for the project.

If the physical bucket changes, business logic should not need to change.

---

## 6. Example resolved paths

Example user config:

```yaml
aws:
  source_bucket: noaa-global-hourly-pds
  project_bucket: syed-datsbd-s2026
```

Example resolved paths:

```bash
paths.raw_isd                  -> s3://noaa-global-hourly-pds
paths.bronze_isd               -> s3://syed-datsbd-s2026/bronze/isd
paths.silver_weather           -> s3://syed-datsbd-s2026/silver/weather
paths.gold_wind_region_daily   -> s3://syed-datsbd-s2026/gold/wind/region/daily
paths.model_registry           -> s3://syed-datsbd-s2026/models/registry
paths.forecast_outputs         -> s3://syed-datsbd-s2026/forecasts/outputs
paths.benchmark_results        -> s3://syed-datsbd-s2026/benchmarks/results
```

---

## 7. Current validation status

The following has been validated on EC2:

* `paths.raw_isd` resolves to the NOAA public source bucket
* NOAA objects can be listed through boto3
* project bucket prefixes resolve correctly
* empty project prefixes correctly return no objects
* S3 path logic works without hardcoded shared bucket assumptions

---

## 8. Output of Layer 4 Part B

This S3 layout provides:

* user-isolated storage
* config-driven cloud portability
* reusable path abstraction for ETL and modeling
* a consistent bucket contract for later bronze/silver/gold workflows
