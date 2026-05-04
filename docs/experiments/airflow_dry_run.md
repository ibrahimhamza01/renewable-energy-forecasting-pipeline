# Airflow DAG Dry Run & Full Execution Guide

## Overview

This document explains how to run the **`wind_pipeline_dag`** in both:

* Dry Run mode (safe, no heavy compute)
* Full Run mode (executes full pipeline)

It also serves as proof of Airflow orchestration for the renewable energy forecasting pipeline.

---

## DAG Description

The Airflow DAG orchestrates the full pipeline:

1. `check_config`
2. `write_bronze`
3. `write_silver`
4. `build_gold_wind_tables`
5. `build_feature_table`
6. `train_model`
7. `evaluate_model`
8. `update_model_registry`
9. `generate_forecasts`
10. `validate_forecasts`

---

## Execution Modes

### 🟡 Dry Run Mode

Used for:

* Testing DAG structure
* Demonstrating orchestration
* Avoiding heavy compute or external dependencies

### How it works

Certain tasks are replaced with safe commands:

```bash
echo "[DRY RUN] Skipping bronze layer"
```

### Example Log Output

```
[DRY RUN] Skipping bronze layer
Command exited with return code 0
```

### Benefits

* Fast execution
* Safe for demos/interviews
* No external data dependencies

---

### Full Run Mode

Used for:

* Actual data processing
* End-to-end pipeline execution

### Example Command

```bash
bash scripts/run_bronze_full_us.sh
```

### Common Issue

If the script is missing:

```
bash: scripts/run_bronze_full_us.sh: No such file or directory
```

### Fix

Ensure:

* Scripts exist inside container
* Correct working directory is set
* Paths are relative to `/opt/airflow/`

---

## How to Trigger the DAG

### Option 1: Airflow UI

1. Open Airflow UI
2. Navigate to `wind_pipeline_dag`
3. Toggle DAG ON
4. Click ▶ **Trigger DAG**

---

### Option 2: CLI

```bash
docker exec -it <airflow-container> airflow dags trigger wind_pipeline_dag
```

---

## Observability (Proof of Execution)

### Key UI Views

#### 1. Graph View

* Shows task dependencies
* Green = success
* Red = failure

#### 2. Gantt View

* Shows execution timeline
* Helps analyze performance

#### 3. Logs

* Per-task execution details
* Useful for debugging

---

## Example Successful Dry Run

* `check_config` → success
* `write_bronze` → dry-run success
* Downstream tasks → executed

---

## Screenshots to Capture

For documentation and interviews:

1. Graph view (all tasks green)
2. Gantt chart
3. `check_config` logs
4. `write_bronze` logs (dry run)

---

## Key Learnings

* Airflow executes tasks inside containers → paths must exist inside container
* Logs are the primary debugging tool
* DAG design should support:

  * safe dry runs
  * full production execution
* Orchestration is separate from business logic

---

## Conclusion

The Airflow DAG successfully demonstrates:

* End-to-end orchestration
* Modular pipeline design
* Debugging via logs
* Safe execution using dry-run mode