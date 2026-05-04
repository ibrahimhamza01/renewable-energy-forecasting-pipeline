from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

import os

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


DEFAULT_ARGS = {
    "owner": "wind-pipeline-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="wind_pipeline_dag",
    description="End-to-end orchestration for the wind energy forecasting pipeline",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["wind", "forecasting", "spark", "noaa", "airflow"],
) as dag:

    check_config = BashOperator(
        task_id="check_config",
        bash_command="""
        echo "Checking active project config..."
        test -n "$PROJECT_USER_CONFIG"
        echo "PROJECT_USER_CONFIG=$PROJECT_USER_CONFIG"
        """,
    )

    write_bronze = BashOperator(
        task_id="write_bronze",
        bash_command=(
            'echo "[DRY RUN] Skipping bronze layer"' if DRY_RUN
            else "bash scripts/run_bronze_full_us.sh "),
    )

    write_silver = BashOperator(
        task_id="write_silver",
        bash_command=(
            'echo "[DRY RUN] Skipping silver layer"' if DRY_RUN
            else "bash scripts/run_silver_full_us.sh "),
    )

    build_gold_wind_tables = BashOperator(
        task_id="build_gold_wind_tables",
        bash_command=(
            'echo "[DRY RUN] Skipping gold layer"' if DRY_RUN
            else "bash scripts/run_gold_full_us.sh "),
    )

    build_feature_table = BashOperator(
        task_id="build_feature_table",
        bash_command=(
            'echo "[DRY RUN] Skipping feature table build"' if DRY_RUN
            else "bash scripts/run_spark_job.sh scripts/build_training_tables.py"),
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command=(
            'echo "[DRY RUN] Skipping model training"' if DRY_RUN
            else "bash scripts/train_gbt.sh "),
    )

    evaluate_model = BashOperator(
        task_id="evaluate_model",
        bash_command=(
            'echo "[DRY RUN] Skipping model evaluation"' if DRY_RUN
            else "bash scripts/run_final_gbt.sh "),
    )

    update_model_registry = BashOperator(
        task_id="update_model_registry",
        bash_command=(
            'echo "[DRY RUN] Skipping model registry update"' if DRY_RUN
            else "bash scripts/register_final_gbt.sh "),
    )

    generate_forecasts = BashOperator(
        task_id="generate_forecasts",
        bash_command=(
            'echo "[DRY RUN] Skipping forecast generation"' if DRY_RUN
            else "bash scripts/generate_forecasts.sh "),
    )
    
    validate_forecasts = BashOperator(
        task_id="validate_forecasts",
        bash_command=(
            'echo "[DRY RUN] Skipping forecast validation"' if DRY_RUN
            else "bash scripts/validate_forecasts.sh "),
    )

    (
        check_config
        >> write_bronze
        >> write_silver
        >> build_gold_wind_tables
        >> build_feature_table
        >> train_model
        >> evaluate_model
        >> update_model_registry
        >> generate_forecasts
        >> validate_forecasts
    )