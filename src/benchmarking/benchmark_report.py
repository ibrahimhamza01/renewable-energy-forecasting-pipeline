# src/benchmarking/benchmark_report.py

from pathlib import Path
import argparse
import pandas as pd


DEFAULT_DUCKDB_PATH = "outputs/benchmark_results/duckdb_benchmarks.csv"
DEFAULT_SPARK_PATH = "outputs/benchmark_results/spark_benchmarks.csv"
DEFAULT_OUTPUT_PATH = "outputs/benchmark_results/benchmark_comparison.csv"


def load_results(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["success"] == True].copy()
    return df


def summarize_results(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["engine", "task_name", "dataset_scale"])
        .agg(
            runs=("run_id", "count"),
            avg_runtime_seconds=("runtime_seconds", "mean"),
            min_runtime_seconds=("runtime_seconds", "min"),
            max_runtime_seconds=("runtime_seconds", "max"),
            median_runtime_seconds=("runtime_seconds", "median"),
            row_count=("row_count", "first"),
        )
        .reset_index()
    )

    return summary


def compare_engines(summary: pd.DataFrame) -> pd.DataFrame:
    pivot = summary.pivot_table(
        index=["task_name", "dataset_scale"],
        columns="engine",
        values="avg_runtime_seconds",
    ).reset_index()

    if "duckdb" in pivot.columns and "spark" in pivot.columns:
        pivot["spark_to_duckdb_runtime_ratio"] = pivot["spark"] / pivot["duckdb"]

        pivot["faster_engine"] = pivot.apply(
            lambda row: "duckdb"
            if row["duckdb"] < row["spark"]
            else "spark",
            axis=1,
        )

    return pivot


def build_benchmark_report(
    duckdb_path: str = DEFAULT_DUCKDB_PATH,
    spark_path: str = DEFAULT_SPARK_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
) -> pd.DataFrame:
    duckdb_df = load_results(duckdb_path)
    spark_df = load_results(spark_path)

    combined = pd.concat([duckdb_df, spark_df], ignore_index=True)

    summary = summarize_results(combined)
    comparison = compare_engines(summary)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(output_path, index=False)

    print(f"Saved benchmark comparison to {output_path}")
    print()
    print(comparison.to_string(index=False))

    return comparison


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build DuckDB vs Spark benchmark report.")

    parser.add_argument("--duckdb-path", default=DEFAULT_DUCKDB_PATH)
    parser.add_argument("--spark-path", default=DEFAULT_SPARK_PATH)
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT_PATH)

    args = parser.parse_args()

    build_benchmark_report(
        duckdb_path=args.duckdb_path,
        spark_path=args.spark_path,
        output_path=args.output_path,
    )