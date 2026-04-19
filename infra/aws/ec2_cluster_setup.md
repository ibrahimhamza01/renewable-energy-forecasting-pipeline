# EC2 Spark Cluster Setup

This document defines how to bootstrap and validate a Spark runtime on EC2 for the
renewable-energy-forecasting-pipeline project.

The goal is to ensure that **the same codebase runs across different users’ EC2 + S3 environments**
without any hardcoded infrastructure assumptions.

---

## Overview

This project uses **Spark standalone mode** on EC2.

Two deployment modes are supported:

### 1. Single-node mode (recommended for development)

- 1 EC2 instance
- acts as:
  - Spark **master**
  - Spark **worker**

### 2. Multi-node mode (scalable)

- 1 EC2 instance → Spark master
- N EC2 instances → Spark workers

---

## Project assumptions

All instructions assume:

- Ubuntu EC2 instances
- repo cloned at:

```bash
/home/ubuntu/renewable-energy-forecasting-pipeline
````

* active config set via:

```bash
export PROJECT_USER_CONFIG=configs/users/<name>.yaml
```

* Spark version is consistent across:

  * EC2 installation
  * Python (`pyspark`)

---

## Configuration model

Each user defines their own environment via:

```
configs/users/<name>.yaml
```

Key fields:

* `aws.project_bucket` → where outputs are written
* `aws.source_bucket` → NOAA public dataset
* `runtime.local_*` → EC2 paths
* `ec2.spark_master_url` → Spark connection

---

## Data architecture

### Source data (read-only)

NOAA public dataset:

```bash
s3://noaa-global-hourly-pds/
```

### Project data (write)

User-owned bucket:

* bronze
* silver
* gold
* models
* forecasts
* benchmarks

No shared buckets. No hardcoded paths.

---

## Required scripts

```
infra/aws/bootstrap/install_dependencies.sh
infra/aws/bootstrap/master_bootstrap.sh
infra/aws/bootstrap/worker_bootstrap.sh
```

---

## EC2 prerequisites

On each EC2 instance:

```bash
# clone repo
git clone <repo-url> /home/ubuntu/renewable-energy-forecasting-pipeline

# create data directory
mkdir -p /home/ubuntu/data

# activate config
cd /home/ubuntu/renewable-energy-forecasting-pipeline
export PROJECT_USER_CONFIG=configs/users/<name>.yaml
```

---

## Network requirements

Minimum ports:

| Port | Purpose          |
| ---- | ---------------- |
| 22   | SSH              |
| 7077 | Spark master RPC |
| 8080 | Spark UI         |

For multi-node:

* workers must reach master on `7077`

---

## Single-node setup (master + worker)

### Step 1 — bootstrap

```bash
bash infra/aws/bootstrap/master_bootstrap.sh
```

This performs:

* dependency install
* environment sync (`uv`)
* Spark installation
* master startup
* worker startup (same node)

---

### Step 2 — verify processes

```bash
jps
```

Expected:

* `Master`
* `Worker`

---

### Step 3 — verify UI

Open:

```
http://localhost:8080
```

(using VS Code port forwarding)

or:

```
http://<ec2-public-host>:8080
```

---

### Step 4 — smoke test

```bash
python - <<'PY'
from src.common.config import config
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("smoke-test")
    .master(config.ec2["spark_master_url"])
    .getOrCreate()
)
PY
```

Expected:

```
+---+---+
| _1| _2|
+---+---+
|  1| ok|
+---+---+
```

---

## Multi-node setup

### Master node

```bash
bash infra/aws/bootstrap/master_bootstrap.sh
```

Capture:

```bash
spark://<master-ip>:7077
```

---

### Worker node(s)

```bash
bash infra/aws/bootstrap/worker_bootstrap.sh spark://<master-ip>:7077
```

---

### Verify cluster

Open Spark UI:

* workers should appear under **Workers**
* cores/memory should be visible

---

## S3 validation

Verify AWS access:

```bash
aws sts get-caller-identity
```

Verify project bucket:

```bash
aws s3 ls s3://<your-bucket>
```

Verify NOAA dataset:

```bash
aws s3 ls s3://noaa-global-hourly-pds/ | head
```

---

## Key rules

### 1. No hardcoded paths

All paths must come from config.

---

### 2. Spark version must match PySpark

Example:

* Spark → 3.5.6
* PySpark → 3.5.6

Mismatch will cause RPC failures.

---

### 3. Master is not compute

Spark master **does not run jobs**.

At least one worker must exist.

---

### 4. Empty S3 bucket is normal

Folders appear only after writes.

---

## Troubleshooting

### Spark UI not loading

Check:

```bash
ss -ltnp | grep 8080
curl http://localhost:8080
```

If localhost works → networking issue.

---

### Job hangs forever

Cause:

```
Initial job has not accepted any resources
```

Fix:

* start worker
* verify worker in UI

---

### Cannot connect to master

Cause:

* wrong master URL
* port 7077 blocked
* Spark not running

---

### PySpark crashes with weird Java errors

Cause:

* Spark version mismatch

Fix:

* align `pyspark` and Spark versions

---

## Validated state

The following is confirmed working:

* EC2 environment setup
* config system loading
* Spark master startup
* Spark worker startup
* PySpark connection to standalone cluster
* successful job execution
* S3 access (public + private)

---

## Output of this layer

You now have:

* a working EC2 Spark runtime
* config-driven execution
* user-isolated cloud environments

This is the foundation for:

* remote job submission
* S3-based pipeline execution
* distributed processing at scale
