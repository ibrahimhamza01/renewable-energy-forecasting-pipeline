# src/benchmarking/benchmark_spark.py

from typing import Dict, Any, List

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.benchmarking.benchmark_runner import (
    BenchmarkResult,
    run_multiple_times,
    save_results,
)


DEFAULT_OUTPUT_PATH = "outputs/benchmark_results/spark_benchmarks.csv"


def create_spark_session(app_name: str = "wind-benchmark-spark") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_weather(spark: SparkSession, path: str):
    return spark.read.parquet(path)


def benchmark_filter_year_region(
    spark: SparkSession,
    input_path: str,
    year: int,
    state: str,
) -> Dict[str, Any]:
    df = read_weather(spark, input_path)

    result_df = (
        df.filter((F.col("year") == year) & (F.col("state") == state))
        .agg(
            F.count("*").alias("row_count"),
            F.avg("wind_speed_ms").alias("avg_wind_speed_ms"),
            F.min("wind_speed_ms").alias("min_wind_speed_ms"),
            F.max("wind_speed_ms").alias("max_wind_speed_ms"),
        )
    )

    row = result_df.collect()[0]
    return {"row_count": int(row["row_count"])}


def benchmark_daily_region_aggregation(
    spark: SparkSession,
    input_path: str,
) -> Dict[str, Any]:
    df = read_weather(spark, input_path)

    result_df = (
        df.withColumn("observation_date", F.to_date("date_utc"))
        .groupBy("observation_date", "region")
        .agg(
            F.count("*").alias("observation_count"),
            F.countDistinct("station_id").alias("station_count"),
            F.avg("wind_speed_ms").alias("avg_wind_speed_ms"),
        )
    )

    return {"row_count": result_df.count()}


def benchmark_station_metadata_join(
    spark: SparkSession,
    weather_path: str,
    metadata_path: str,
) -> Dict[str, Any]:
    weather_df = read_weather(spark, weather_path)

    if metadata_path.endswith(".csv"):
        metadata_df = (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .csv(metadata_path)
        )
    else:
        metadata_df = spark.read.parquet(metadata_path)

    joined_df = (
        weather_df.alias("w")
        .join(
            metadata_df.alias("m"),
            F.col("w.station_id") == F.col("m.station_id"),
            "inner",
        )
        .filter(F.col("m.state").isNotNull())
        .select(
            F.col("w.station_id"),
            F.col("w.date_utc"),
            F.col("m.state"),
            F.col("m.region"),
            F.col("w.wind_speed_ms"),
        )
    )

    return {"row_count": joined_df.count()}


def benchmark_grouped_temporal_summaries(
    spark: SparkSession,
    input_path: str,
) -> Dict[str, Any]:
    df = read_weather(spark, input_path)

    result_df = (
        df.groupBy("year", "month", "state")
        .agg(
            F.count("*").alias("observation_count"),
            F.countDistinct("station_id").alias("station_count"),
            F.avg("wind_speed_ms").alias("avg_wind_speed_ms"),
            F.min("wind_speed_ms").alias("min_wind_speed_ms"),
            F.max("wind_speed_ms").alias("max_wind_speed_ms"),
        )
    )

    return {"row_count": result_df.count()}


def run_spark_benchmarks(
    weather_path: str,
    metadata_path: str | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    dataset_scale: str = "small",
    year: int = 2020,
    state: str = "TX",
    n_runs: int = 3,
) -> List[BenchmarkResult]:
    spark = create_spark_session()
    results: List[BenchmarkResult] = []

    results.extend(
        run_multiple_times(
            engine="spark",
            task_name="filter_year_region",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_filter_year_region(
                spark=spark,
                input_path=weather_path,
                year=year,
                state=state,
            ),
            n_runs=n_runs,
        )
    )

    results.extend(
        run_multiple_times(
            engine="spark",
            task_name="daily_region_aggregation",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_daily_region_aggregation(
                spark=spark,
                input_path=weather_path,
            ),
            n_runs=n_runs,
        )
    )

    if metadata_path:
        results.extend(
            run_multiple_times(
                engine="spark",
                task_name="station_metadata_join",
                dataset_scale=dataset_scale,
                func=lambda: benchmark_station_metadata_join(
                    spark=spark,
                    weather_path=weather_path,
                    metadata_path=metadata_path,
                ),
                n_runs=n_runs,
            )
        )

    results.extend(
        run_multiple_times(
            engine="spark",
            task_name="grouped_temporal_summaries",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_grouped_temporal_summaries(
                spark=spark,
                input_path=weather_path,
            ),
            n_runs=n_runs,
        )
    )

    save_results(results, output_path)
    spark.stop()

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Spark benchmarks.")

    parser.add_argument("--weather-path", required=True)
    parser.add_argument("--metadata-path", required=False)
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--dataset-scale", default="small")
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--state", default="TX")
    parser.add_argument("--n-runs", type=int, default=3)

    args = parser.parse_args()

    run_spark_benchmarks(
        weather_path=args.weather_path,
        metadata_path=args.metadata_path,
        output_path=args.output_path,
        dataset_scale=args.dataset_scale,
        year=args.year,
        state=args.state,
        n_runs=args.n_runs,
    )