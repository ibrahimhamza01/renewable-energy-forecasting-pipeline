# src/ingestion/discover_isd_files.py

from pathlib import Path
import pandas as pd
import re

CORE_COLUMNS = [
    "STATION", "DATE", "SOURCE", "LATITUDE", "LONGITUDE", "ELEVATION",
    "NAME", "REPORT_TYPE", "QUALITY_CONTROL",
    "WND", "CIG", "VIS", "TMP", "DEW", "SLP"
]

def find_csv_files(root: str):
    root_path = Path(root)
    return sorted(root_path.rglob("*.csv"))

def extract_years(paths):
    years = set()
    for p in paths:
        m = re.search(r"(19|20)\d{2}", str(p))
        if m:
            years.add(m.group(0))
    return sorted(years)

def inspect_sample_file(file_path: str, nrows: int = 20):
    df = pd.read_csv(file_path, nrows=nrows)
    cols = list(df.columns)
    missing_core = [c for c in CORE_COLUMNS if c not in cols]
    extra_cols = [c for c in cols if c not in CORE_COLUMNS]
    return {
        "columns": cols,
        "missing_core": missing_core,
        "extra_cols": extra_cols,
        "sample_row_count": len(df),
    }

if __name__ == "__main__":
    # Replace with your local sample root
    data_root = "data/raw/isd_sample"

    files = find_csv_files(data_root)
    print(f"Total CSV files found: {len(files)}")

    sample_files = files[:10]
    print("\nSample files:")
    for f in sample_files:
        print(f)

    years = extract_years(files)
    print("\nDetected years:")
    print(years[:20], "...", years[-5:] if years else [])

    if files:
        result = inspect_sample_file(str(files[0]), nrows=20)
        print("\nColumns:")
        print(result["columns"])

        print("\nMissing core columns:")
        print(result["missing_core"])

        print("\nExtra columns:")
        print(result["extra_cols"])

        print("\nSample row count:")
        print(result["sample_row_count"])