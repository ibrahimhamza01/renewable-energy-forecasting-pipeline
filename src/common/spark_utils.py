"""
Utility functions for creating and managing Spark sessions.

This module provides a standardized way to create Spark sessions
from the project Spark configuration file for local development
and testing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pyspark.sql import SparkSession


DEFAULT_SPARK_CONFIG_PATH = Path("configs/spark_config.yaml")


def _load_spark_config(config_path: Path = DEFAULT_SPARK_CONFIG_PATH) -> dict[str, Any]:
    """
    Load Spark configuration from YAML.

    Parameters
    ----------
    config_path : Path
        Path to the Spark configuration YAML file.

    Returns
    -------
    dict[str, Any]
        Parsed Spark configuration dictionary.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Spark config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if "spark" not in config:
        raise KeyError(f"Missing top-level 'spark' key in config file: {config_path}")

    return config["spark"]


def get_local_spark_session(
    app_name: str | None = None,
    config_path: Path = DEFAULT_SPARK_CONFIG_PATH,
) -> SparkSession:
    """
    Create or retrieve a local Spark session using YAML config.

    Parameters
    ----------
    app_name : str | None
        Optional Spark application name override.
    config_path : Path
        Path to the Spark configuration YAML file.

    Returns
    -------
    SparkSession
        A Spark session configured for local execution.
    """
    spark_cfg = _load_spark_config(config_path)

    configured_app_name = app_name or spark_cfg.get("app_name", "wind-energy-local")
    configured_master = spark_cfg.get("master", "local[*]")
    configured_options = spark_cfg.get("config", {})

    warehouse_dir = Path("outputs/spark_warehouse").resolve()
    warehouse_uri = warehouse_dir.as_uri()

    builder = (
        SparkSession.builder
        .appName(configured_app_name)
        .master(configured_master)
    )

    for key, value in configured_options.items():
        builder = builder.config(key, str(value))

    # Local filesystem settings needed for local Parquet writes.
    builder = (
        builder
        .config("spark.sql.warehouse.dir", warehouse_uri)
        .config("spark.hadoop.fs.defaultFS", "file:///")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    return spark


def stop_spark_session(spark: SparkSession) -> None:
    """
    Stop a Spark session safely.

    Parameters
    ----------
    spark : SparkSession
        The Spark session to stop.
    """
    if spark is not None:
        spark.stop()