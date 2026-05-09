from pathlib import Path
import json
import shutil

import pandas as pd
import yaml


CONFIG_PATH = Path("configs/website_config.yaml")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def copy_validated_csv(src: Path, dest: Path, required_columns: list[str]) -> bool:
    if not src.exists():
        print(f"Missing CSV: {src}")
        return False

    df = pd.read_csv(src)

    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        print(f"Invalid CSV schema: {src}")
        print(f"Missing columns: {missing_cols}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"Copied CSV {src} -> {dest}")
    return True


def copy_json(src: Path, dest: Path, optional: bool = False) -> bool:
    if not src.exists():
        message = f"Missing JSON: {src}"
        if optional:
            print(f"{message} (optional)")
            return True
        print(message)
        return False

    with src.open("r", encoding="utf-8") as f:
        json.load(f)

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"Copied JSON {src} -> {dest}")
    return True


def write_json(dest: Path, payload: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote JSON {dest}")


def main() -> None:
    config = load_config()
    website_cfg = config["website"]

    output_dir = Path(website_cfg["artifact_roots"]["website_data_dir"])

    failures = []

    for artifact in website_cfg["candidate_data_artifacts"]:
        src = Path(artifact["source"])
        dest = output_dir / artifact["output_name"]
        ok = copy_validated_csv(src, dest, artifact["required_columns"])
        if not ok:
            failures.append(str(src))

    for artifact in website_cfg["metrics_artifacts"]:
        src = Path(artifact["source"])
        dest = output_dir / artifact["output_name"]
        optional = artifact.get("optional", False)
        ok = copy_json(src, dest, optional=optional)
        if not ok:
            failures.append(str(src))

    station_payload = website_cfg["live_stations"]["stations"]
    write_json(output_dir / "live_station_list.json", station_payload)

    pipeline_summary = {
        "project_name": website_cfg["name"],
        "mode": website_cfg["mode"],
        "dataset": "NOAA Integrated Surface Database (ISD)",
        "raw_scale": "600GB+ uncompressed",
        "global_station_count": "35,000+",
        "geographic_scope": "Contiguous United States",
        "time_window": "1995-2025",
        "processing_engine": "PySpark",
        "orchestration": "Apache Airflow",
        "benchmarking": "DuckDB vs Spark",
        "final_model": "final_tuned_gbt",
        "deployment_goal": "Website works without EC2/S3 after artifact export",
    }
    write_json(output_dir / "pipeline_summary.json", pipeline_summary)

    print("\nExport summary:")
    if failures:
        print("FAILED artifacts:")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)

    print("All required website artifacts exported successfully.")


if __name__ == "__main__":
    main()