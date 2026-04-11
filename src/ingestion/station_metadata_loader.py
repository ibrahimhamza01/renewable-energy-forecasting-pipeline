# src/ingestion/station_metadata_loader.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class StationMetadataPaths:
    isd_history_csv: str = "data/raw/noaa_metadata/isd-history.csv"


REQUIRED_COLUMNS = [
    "USAF",
    "WBAN",
    "STATION NAME",
    "CTRY",
    "STATE",
    "LAT",
    "LON",
    "ELEV(M)",
    "BEGIN",
    "END",
]

OUTPUT_COLUMNS = [
    "station_id",
    "station_name",
    "country_code",
    "state",
    "latitude",
    "longitude",
    "elevation_m",
    "begin_date",
    "end_date",
    "begin_year",
    "end_year",
]


def build_station_id(usaf: object, wban: object) -> str:
    usaf_str = str(usaf).strip()
    wban_str = str(wban).strip()
    return f"{usaf_str}{wban_str}"


def parse_yyyymmdd(value: object) -> Optional[pd.Timestamp]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text == "nan":
        return None
    try:
        return pd.to_datetime(text, format="%Y%m%d", errors="coerce")
    except Exception:
        return None


def load_station_metadata(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Station metadata file not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in station metadata: {missing}")

    df = df[REQUIRED_COLUMNS].copy()

    df["station_id"] = df.apply(
        lambda row: build_station_id(row["USAF"], row["WBAN"]),
        axis=1,
    )
    df["station_name"] = df["STATION NAME"].str.strip()
    df["country_code"] = df["CTRY"].str.strip()
    df["state"] = df["STATE"].fillna("").str.strip()

    df["latitude"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["LON"], errors="coerce")
    df["elevation_m"] = pd.to_numeric(df["ELEV(M)"], errors="coerce")

    df["begin_date"] = df["BEGIN"].apply(parse_yyyymmdd)
    df["end_date"] = df["END"].apply(parse_yyyymmdd)

    df["begin_year"] = df["begin_date"].dt.year
    df["end_year"] = df["end_date"].dt.year

    df = df[OUTPUT_COLUMNS].copy()

    # Drop rows that cannot support geospatial scope filtering
    df = df.dropna(subset=["station_id", "latitude", "longitude"])

    # Keep one row per station_id if duplicates exist
    df = df.sort_values(["station_id", "end_year", "begin_year"], ascending=[True, False, True])
    df = df.drop_duplicates(subset=["station_id"], keep="first").reset_index(drop=True)

    return df


if __name__ == "__main__":
    paths = StationMetadataPaths()
    stations = load_station_metadata(paths.isd_history_csv)

    print(f"Loaded stations: {len(stations)}")
    print("\nColumns:")
    print(list(stations.columns))

    print("\nSample rows:")
    print(stations.head(10).to_string(index=False))

    print("\nCountry counts (top 10):")
    print(stations["country_code"].value_counts(dropna=False).head(10))