from pathlib import Path
import shutil


FIGURES = {
    "outputs/figures/forecast_vs_actual.png": "forecast_vs_actual.png",
    "outputs/figures/regional_wind_trends.png": "regional_wind_trends.png",
    "outputs/figures/seasonal_trends.png": "seasonal_trends.png",
    "outputs/figures/us_wind_potential_map.png": "us_wind_potential_map.png",
    "outputs/figures/benchmark_comparison.png": "benchmark_comparison.png",
    "docs/experiments/airflow/airflow_dag_graph_success.png": "airflow_dag_graph_success.png",
}


DESTINATIONS = [
    Path("docs/assets"),
    Path("website/public/assets"),
]


def copy_file(src: Path, dest_dir: Path, output_name: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / output_name
    shutil.copy2(src, dest)
    print(f"Copied {src} -> {dest}")


def main() -> None:
    missing = []

    for src_str, output_name in FIGURES.items():
        src = Path(src_str)

        if not src.exists():
            missing.append(src_str)
            print(f"Missing: {src_str}")
            continue

        for dest_dir in DESTINATIONS:
            copy_file(src, dest_dir, output_name)

    print("\nCopy complete.")

    if missing:
        print("\nMissing files:")
        for item in missing:
            print(f"- {item}")

        print("\nThese are not fatal yet, but should be created or exported before final deployment.")


if __name__ == "__main__":
    main()