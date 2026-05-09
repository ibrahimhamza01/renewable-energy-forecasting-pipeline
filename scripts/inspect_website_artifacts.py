from pathlib import Path

import pandas as pd
import yaml


CONFIG_PATH = Path("configs/website_config.yaml")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def inspect_csv(path: Path, required_columns: list[str]) -> bool:
    print("\n" + "=" * 80)
    print(f"CSV: {path}")

    if not path.exists():
        print("STATUS: MISSING")
        return False

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"STATUS: FAILED TO READ ({exc})")
        return False

    print(f"STATUS: READABLE")
    print(f"ROWS: {len(df)}")
    print(f"COLUMNS: {list(df.columns)}")

    missing_cols = [c for c in required_columns if c not in df.columns]

    if missing_cols:
        print(f"SCHEMA: FAIL")
        print(f"MISSING COLUMNS: {missing_cols}")
        return False

    print("SCHEMA: PASS")

    print("\nHEAD:")
    print(df.head(5).to_string(index=False))

    print("\nNULL COUNTS:")
    print(df[required_columns].isna().sum().to_string())

    return True


def main() -> None:
    config = load_config()
    artifacts = config["website"]["candidate_data_artifacts"]

    results = []

    for artifact in artifacts:
        path = Path(artifact["source"])
        required_columns = artifact["required_columns"]
        ok = inspect_csv(path, required_columns)
        results.append((str(path), ok))

    print("\n" + "=" * 80)
    print("SUMMARY")

    for path, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {path}")


if __name__ == "__main__":
    main()