# src/benchmarking/benchmark_duckdb.py

from typing import Dict, Any, List

import duckdb

from src.benchmarking.benchmark_runner import (
    BenchmarkResult,
    run_multiple_times,
    save_results,
)


DEFAULT_OUTPUT_PATH = "outputs/benchmark_results/duckdb_benchmarks.csv"


def connect_duckdb() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")


def parquet_scan(path: str) -> str:
    return f"read_parquet('{path}/**/*.parquet', hive_partitioning=true)"


def benchmark_filter_year_region(
    conn: duckdb.DuckDBPyConnection,
    input_path: str,
    year: int,
    state: str,
) -> Dict[str, Any]:
    query = f"""
        SELECT
            COUNT(*) AS row_count,
            AVG(wind_speed_ms) AS avg_wind_speed_ms,
            MIN(wind_speed_ms) AS min_wind_speed_ms,
            MAX(wind_speed_ms) AS max_wind_speed_ms
        FROM {parquet_scan(input_path)}
        WHERE year = {year}
          AND state = '{state}'
    """

    row = conn.execute(query).fetchone()
    return {"row_count": int(row[0]) if row and row[0] is not None else 0}


def benchmark_daily_region_aggregation(
    conn: duckdb.DuckDBPyConnection,
    input_path: str,
) -> Dict[str, Any]:
    query = f"""
        SELECT
            CAST(date_utc AS DATE) AS observation_date,
            region,
            COUNT(*) AS observation_count,
            COUNT(DISTINCT station_id) AS station_count,
            AVG(wind_speed_ms) AS avg_wind_speed_ms
        FROM {parquet_scan(input_path)}
        GROUP BY
            CAST(date_utc AS DATE),
            region
    """

    result = conn.execute(query).fetchall()
    return {"row_count": len(result)}


def benchmark_station_metadata_join(
    conn: duckdb.DuckDBPyConnection,
    weather_path: str,
    metadata_path: str,
) -> Dict[str, Any]:
    query = f"""
        SELECT
            w.station_id,
            w.date_utc,
            m.state,
            m.region,
            w.wind_speed_ms
        FROM {parquet_scan(weather_path)} w
        INNER JOIN {parquet_scan(metadata_path)} m
            ON w.station_id = m.station_id
        WHERE m.state IS NOT NULL
    """

    result = conn.execute(query).fetchall()
    return {"row_count": len(result)}


def benchmark_grouped_temporal_summaries(
    conn: duckdb.DuckDBPyConnection,
    input_path: str,
) -> Dict[str, Any]:
    query = f"""
        SELECT
            year,
            month,
            state,
            COUNT(*) AS observation_count,
            COUNT(DISTINCT station_id) AS station_count,
            AVG(wind_speed_ms) AS avg_wind_speed_ms,
            MIN(wind_speed_ms) AS min_wind_speed_ms,
            MAX(wind_speed_ms) AS max_wind_speed_ms
        FROM {parquet_scan(input_path)}
        GROUP BY
            year,
            month,
            state
    """

    result = conn.execute(query).fetchall()
    return {"row_count": len(result)}


def run_duckdb_benchmarks(
    weather_path: str,
    metadata_path: str | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    dataset_scale: str = "small",
    year: int = 2020,
    state: str = "TX",
    n_runs: int = 3,
) -> List[BenchmarkResult]:
    conn = connect_duckdb()
    results: List[BenchmarkResult] = []

    results.extend(
        run_multiple_times(
            engine="duckdb",
            task_name="filter_year_region",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_filter_year_region(conn, weather_path, year, state),
            n_runs=n_runs,
        )
    )

    results.extend(
        run_multiple_times(
            engine="duckdb",
            task_name="daily_region_aggregation",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_daily_region_aggregation(conn, weather_path),
            n_runs=n_runs,
        )
    )

    if metadata_path:
        results.extend(
            run_multiple_times(
                engine="duckdb",
                task_name="station_metadata_join",
                dataset_scale=dataset_scale,
                func=lambda: benchmark_station_metadata_join(
                    conn, weather_path, metadata_path
                ),
                n_runs=n_runs,
            )
        )

    results.extend(
        run_multiple_times(
            engine="duckdb",
            task_name="grouped_temporal_summaries",
            dataset_scale=dataset_scale,
            func=lambda: benchmark_grouped_temporal_summaries(conn, weather_path),
            n_runs=n_runs,
        )
    )

    save_results(results, output_path)
    conn.close()

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run DuckDB benchmarks.")
    parser.add_argument("--weather-path", required=True)
    parser.add_argument("--metadata-path", required=False)
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--dataset-scale", default="small")
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--state", default="TX")
    parser.add_argument("--n-runs", type=int, default=3)

    args = parser.parse_args()

    run_duckdb_benchmarks(
        weather_path=args.weather_path,
        metadata_path=args.metadata_path,
        output_path=args.output_path,
        dataset_scale=args.dataset_scale,
        year=args.year,
        state=args.state,
        n_runs=args.n_runs,
    )