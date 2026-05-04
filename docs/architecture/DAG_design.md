# Airflow DAG Design — Wind Energy Forecasting Pipeline

## Goal

Use Apache Airflow to orchestrate the wind forecasting pipeline end to end.

The DAG should not contain business logic. Each task should call existing scripts or modules from the pipeline.

## DAG Name

`wind_pipeline_dag`

## Pipeline Tasks

1. `check_config`
   - Verify `PROJECT_USER_CONFIG` is set.
   - Verify config can be loaded.

2. `ingest_raw_isd`
   - Discover/read NOAA ISD raw input.
   - Prepare raw data for bronze.

3. `write_bronze`
   - Write compacted bronze layer.

4. `write_silver`
   - Parse, clean, QC-filter, standardize units, and enrich metadata.

5. `build_gold_wind_tables`
   - Generate daily/monthly wind analytics tables.

6. `build_feature_table`
   - Generate lag, rolling, temporal, and regional features.

7. `train_model`
   - Train candidate or selected model.

8. `evaluate_model`
   - Compute RMSE, MAE, bias, and validation metrics.

9. `update_model_registry`
   - Save approved model and metadata.

10. `generate_forecasts`
   - Generate batch wind forecasts.

11. `validate_forecasts`
   - Validate schema, nulls, prediction bounds, and output sanity.

## Dependency Graph

```text
check_config
    ↓
ingest_raw_isd
    ↓
write_bronze
    ↓
write_silver
    ↓
build_gold_wind_tables
    ↓
build_feature_table
    ↓
train_model
    ↓
evaluate_model
    ↓
update_model_registry
    ↓
generate_forecasts
    ↓
validate_forecasts
````

## Design Rules

* DAG code only orchestrates tasks.
* Business logic stays in `src/` and `scripts/`.
* All paths come from config.
* No hardcoded S3 bucket names.
* No hardcoded EC2 hostnames.
* No hardcoded local paths.
* Airflow must use the same config system as local and Spark runs.
* Each task should be individually runnable outside Airflow.

## First Airflow Implementation Strategy

Start with a local dry-run DAG that uses `BashOperator`.

Each task should call a script, for example:

```bash
bash scripts/run_spark_job.sh <job_name>
```

Later, the same DAG can be moved to EC2/Airflow runtime.

## Initial DAG Schedule

Manual trigger only (no automatic scheduling during development):

```python
schedule = None
```

This avoids accidental large cloud runs while testing.

## Retry Policy

Recommended default:

* retries: 1
* retry delay: 5 minutes
* catchup: false

## Completion Criteria

Layer 11 Part A is complete when:

* `docs/architecture/DAG_design.md` exists.
* DAG task list is defined.
* Dependencies are clear.
* No task embeds business logic.
* The design supports config-driven execution.
