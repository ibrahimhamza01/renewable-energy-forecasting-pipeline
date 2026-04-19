# Cloud Execution Architecture

## Overview

This project supports **config-driven, user-isolated cloud execution** of Spark jobs on AWS infrastructure.

Each user runs the same codebase against:

* their own EC2 instance(s)
* their own S3 bucket
* their own runtime configuration

This ensures:

* reproducibility
* portability across environments
* no hardcoded infrastructure dependencies

---

## Core Principles

### 1. Config-Driven Execution

All cloud behavior is controlled via:

* `configs/users/<user>.yaml`
* `configs/spark_config.yaml`
* environment variable:

  ```
  PROJECT_USER_CONFIG
  ```

No code contains hardcoded:

* S3 bucket names
* EC2 hostnames
* Spark master URLs

---

### 2. User-Isolated Infrastructure

Each user defines:

```yaml
aws:
  project_bucket: <user-specific-bucket>

ec2:
  spark_master_url: spark://<user-ec2-ip>:7077
```

Result:

* independent S3 storage
* independent Spark cluster
* no shared state between users

---

### 3. Logical Path Abstraction

All data paths are resolved through:

* `configs/paths.yaml`
* `src/common/paths.py`

Examples:

| Layer  | Example Path                         |
| ------ | ------------------------------------ |
| Raw    | `s3a://noaa-global-hourly-pds`       |
| Bronze | `s3a://<user-bucket>/bronze/isd`     |
| Silver | `s3a://<user-bucket>/silver/weather` |
| Gold   | `s3a://<user-bucket>/gold/...`       |

This guarantees:

* portability across users
* consistent data layout

---

## Execution Workflow

### Step 1 — Bootstrap Environment

```bash
bash scripts/bootstrap_repo.sh
```

This:

* activates virtual environment
* loads `.env`
* validates config
* prints resolved paths

---

### Step 2 — Submit Spark Job

```bash
bash scripts/run_spark_job.sh <python_file>
```

Example:

```bash
bash scripts/run_spark_job.sh scripts/smoke_test_remote_spark.py
```

---

### Step 3 — Spark Job Execution

`spark-submit` is used with:

* config-driven master URL
* dependency injection (`--packages`)
* dynamic Spark configs (`--conf`)

Example (simplified):

```bash
spark-submit \
  --master spark://<ec2-ip>:7077 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  ...
```

---

### Step 4 — Output to S3

Jobs write to:

```
s3a://<user-bucket>/<layer>/<dataset>
```

Example:

```
s3a://syed-datsbd-s2026/bronze/isd/_smoke_test/
```

---

## Spark Configuration

Defined in:

```
configs/spark_config.yaml
```

Includes:

* execution settings
* memory allocation
* S3A configuration
* dependency packages

Key settings:

```yaml
spark.jars.packages: org.apache.hadoop:hadoop-aws:3.3.4

spark.hadoop.fs.s3a.impl: org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.aws.credentials.provider: com.amazonaws.auth.InstanceProfileCredentialsProvider
```

---

## AWS Integration

### Credentials

Authentication is handled via:

* EC2 instance role (IAM)

No credentials are stored in:

* code
* config files
* environment variables

---

### Data Sources

| Type         | Location                       |
| ------------ | ------------------------------ |
| Raw NOAA ISD | `s3a://noaa-global-hourly-pds` |
| Project Data | `s3a://<user-bucket>/...`      |

---

## Spark Cluster Architecture

Single-node standalone cluster (current setup):

```
EC2 Instance
 ├── Spark Master (port 7077)
 ├── Spark Worker
 └── Driver (spark-submit)
```

Web UI:

```
http://<ec2-public-host>:8080
```

---

## Validation (Smoke Test)

A minimal remote job was executed:

* created DataFrame
* ran Spark transformations
* wrote Parquet output to S3

Output verified:

```
_SUCCESS
part-*.parquet
```

This confirms:

* cluster connectivity
* executor allocation
* S3 write capability
* dependency resolution (S3A)

---

## Failure Modes & Fixes

| Issue                                   | Cause                  | Fix                |
| --------------------------------------- | ---------------------- | ------------------ |
| `No FileSystem for scheme "s3"`         | using `s3://`          | switch to `s3a://` |
| `ClassNotFoundException: S3AFileSystem` | missing Hadoop AWS jar | use `--packages`   |
| No executors                            | worker not started     | start worker       |
| Cannot connect to master                | wrong IP               | use private EC2 IP |

---

## Summary

This architecture provides:

* fully portable cloud execution
* per-user infrastructure isolation
* config-driven path resolution
* reproducible Spark job execution

The system is now ready for:

* large-scale data ingestion
* distributed transformations
* model training workflows