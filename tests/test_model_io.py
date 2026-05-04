from pyspark.sql import functions as F

from src.common.spark_utils import get_spark_session
from src.reporting.export_metrics import resolve_path


REQUIRED_FORECAST_COLUMNS = {
    "forecast_id",
    "forecast_date",
    "region",
    "state",
    "target_name",
    "prediction",
    "model_name",
    "model_version",
    "generation_timestamp",
    "horizon_days",
}


def latest_forecast_run_path(spark):
    forecast_base = resolve_path("forecasts", "outputs")

    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    fs = spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem.get(
        spark.sparkContext._jvm.java.net.URI.create(forecast_base),
        hadoop_conf,
    )
    base_path = spark.sparkContext._jvm.org.apache.hadoop.fs.Path(forecast_base)

    statuses = fs.listStatus(base_path)

    run_paths = [
        status.getPath().toString()
        for status in statuses
        if status.isDirectory()
        and status.getPath().getName().startswith("run_id=")
        and not status.getPath().getName().endswith("_metadata")
    ]

    if not run_paths:
        raise FileNotFoundError(f"No forecast run_id folders found under {forecast_base}")

    return sorted(run_paths)[-1]


def load_latest_forecast_df():
    spark = get_spark_session()
    run_path = latest_forecast_run_path(spark)
    return spark.read.parquet(run_path)


def test_forecast_schema_latest_run():
    df = load_latest_forecast_df()

    missing = REQUIRED_FORECAST_COLUMNS - set(df.columns)

    assert not missing, f"Missing forecast columns: {missing}"


def test_forecast_required_fields_not_null():
    df = load_latest_forecast_df()

    required_non_null = [
        "forecast_id",
        "forecast_date",
        "state",
        "target_name",
        "prediction",
        "model_name",
        "model_version",
        "generation_timestamp",
        "horizon_days",
    ]

    null_counts = (
        df.select(
            *[
                F.count(F.when(F.col(c).isNull(), c)).alias(c)
                for c in required_non_null
            ]
        )
        .collect()[0]
        .asDict()
    )

    bad = {k: v for k, v in null_counts.items() if v > 0}

    assert not bad, f"Unexpected nulls in forecast output: {bad}"


def test_forecast_prediction_range():
    df = load_latest_forecast_df()

    stats = (
        df.agg(
            F.min("prediction").alias("min_prediction"),
            F.max("prediction").alias("max_prediction"),
        )
        .collect()[0]
        .asDict()
    )

    assert stats["min_prediction"] >= 0.0
    assert stats["max_prediction"] <= 1.0


def test_forecast_has_model_version():
    df = load_latest_forecast_df()

    model_versions = df.select("model_version").distinct().count()

    assert model_versions >= 1