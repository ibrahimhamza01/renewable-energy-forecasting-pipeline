"""
Utility functions for creating and managing Spark sessions.

This module provides a standardized, config-driven way to create Spark sessions
for both local development and EC2 standalone Spark execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession

from src.common.config import config


def _get_shared_spark_config() -> dict[str, Any]:
    """
    Return the shared Spark configuration dictionary loaded from config.

    Expected structure in configs/spark_config.yaml:
        spark:
          app_name: ...
          master: ...
          config:
            spark.some.option: value
    """
    spark_cfg = config.spark or {}

    if "spark" not in spark_cfg:
        raise KeyError("Missing top-level 'spark' key in configs/spark_config.yaml")

    return spark_cfg["spark"]


def _apply_spark_options(
    builder: SparkSession.Builder,
    options: dict[str, Any],
) -> SparkSession.Builder:
    """
    Apply Spark configuration key/value pairs to a SparkSession builder.
    """
    for key, value in options.items():
        builder = builder.config(key, str(value))
    return builder


def get_spark_session(
    app_name: str | None = None,
    master: str | None = None,
) -> SparkSession:
    """
    Create or retrieve a Spark session using shared config plus active user config.

    Parameters
    ----------
    app_name : str | None
        Optional Spark application name override.
    master : str | None
        Optional Spark master override. If omitted, uses the active user config
        value from config.ec2["spark_master_url"], falling back to the shared
        Spark config master, then to local[*].

    Returns
    -------
    SparkSession
        A Spark session configured for local or remote execution.
    """
    spark_cfg = _get_shared_spark_config()

    configured_app_name = app_name or spark_cfg.get("app_name", "wind-energy-pipeline")
    configured_master = (
        master
        or config.ec2.get("spark_master_url")
        or spark_cfg.get("master")
        or "local[*]"
    )
    configured_options = spark_cfg.get("config", {})

    builder = (
        SparkSession.builder
        .appName(configured_app_name)
        .master(configured_master)
    )

    builder = _apply_spark_options(builder, configured_options)

    is_local = configured_master.startswith("local")

    if is_local:
        warehouse_dir = (config.project_root / "outputs" / "spark_warehouse").resolve()
        warehouse_dir.mkdir(parents=True, exist_ok=True)
        warehouse_uri = warehouse_dir.as_uri()

        builder = (
            builder
            .config("spark.sql.warehouse.dir", warehouse_uri)
            .config("spark.hadoop.fs.defaultFS", "file:///")
            .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    return spark


def get_local_spark_session(app_name: str | None = None) -> SparkSession:
    """
    Create a Spark session explicitly in local mode.

    Parameters
    ----------
    app_name : str | None
        Optional Spark application name override.

    Returns
    -------
    SparkSession
        A Spark session forced to local[*].
    """
    return get_spark_session(app_name=app_name, master="local[*]")


def get_remote_spark_session(app_name: str | None = None) -> SparkSession:
    """
    Create a Spark session using the active user config Spark master URL.

    Parameters
    ----------
    app_name : str | None
        Optional Spark application name override.

    Returns
    -------
    SparkSession
        A Spark session configured for remote standalone Spark execution.
    """
    remote_master = config.ec2.get("spark_master_url")
    if not remote_master:
        raise ValueError("Missing ec2.spark_master_url in active user config")

    return get_spark_session(app_name=app_name, master=remote_master)


def stop_spark_session(spark: SparkSession | None) -> None:
    """
    Stop a Spark session safely.
    """
    if spark is not None:
        spark.stop()