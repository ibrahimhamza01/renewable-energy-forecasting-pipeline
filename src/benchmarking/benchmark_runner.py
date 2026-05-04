# src/benchmarking/benchmark_runner.py

import time
import uuid
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, List
import pandas as pd
from pathlib import Path


# -----------------------------
# Benchmark result schema
# -----------------------------

@dataclass
class BenchmarkResult:
    run_id: str
    engine: str
    task_name: str
    dataset_scale: str

    start_time: float
    end_time: float
    runtime_seconds: float

    row_count: int | None
    notes: str

    success: bool
    error_message: str | None


# -----------------------------
# Timer wrapper
# -----------------------------

def run_benchmark_task(
    engine: str,
    task_name: str,
    dataset_scale: str,
    func: Callable[[], Dict[str, Any]],
    notes: str = "",
) -> BenchmarkResult:
    """
    Runs a benchmark task and measures execution time.

    func must return:
        {
            "row_count": int (optional)
        }
    """

    run_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        output = func()
        success = True
        error_message = None

    except Exception as e:
        output = {}
        success = False
        error_message = str(e)

    end_time = time.time()

    return BenchmarkResult(
        run_id=run_id,
        engine=engine,
        task_name=task_name,
        dataset_scale=dataset_scale,
        start_time=start_time,
        end_time=end_time,
        runtime_seconds=end_time - start_time,
        row_count=output.get("row_count"),
        notes=notes,
        success=success,
        error_message=error_message,
    )


# -----------------------------
# Multiple runs helper
# -----------------------------

def run_multiple_times(
    engine: str,
    task_name: str,
    dataset_scale: str,
    func: Callable[[], Dict[str, Any]],
    n_runs: int = 3,
) -> List[BenchmarkResult]:

    results = []

    for i in range(n_runs):
        result = run_benchmark_task(
            engine=engine,
            task_name=task_name,
            dataset_scale=dataset_scale,
            func=func,
            notes=f"run_{i+1}",
        )
        results.append(result)

    return results


# -----------------------------
# Result writer
# -----------------------------

def save_results(
    results: List[BenchmarkResult],
    output_path: str,
):
    """
    Saves benchmark results to CSV.
    """

    records = [asdict(r) for r in results]
    df = pd.DataFrame(records)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"Saved benchmark results to {output_path}")