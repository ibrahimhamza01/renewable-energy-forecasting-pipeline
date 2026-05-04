# Airflow Orchestration – Wind Forecasting Pipeline

## Overview
This DAG orchestrates the full pipeline:
Bronze → Silver → Gold → Feature Engineering → Model Training → Forecasting

## Features
- Config-driven execution (`PROJECT_USER_CONFIG`)
- Dry-run mode for safe testing
- Modular BashOperator tasks
- Dockerized Airflow deployment

## Evidence
- DAG graph showing dependencies
- Successful DAG runs
- Logs confirming config injection
- Dry-run execution validation