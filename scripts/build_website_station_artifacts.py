from pathlib import Path
import json
import math

import pandas as pd


SOURCE_CSV = Path("website/public/data/us_wind_station_map.csv")
ISD_HISTORY_CSV = Path("data/raw/noaa_metadata/isd-history.csv")

OUTPUT_DIR = Path("website/public/data")
ALL_PIPELINE_STATIONS_OUT = OUTPUT_DIR / "all_pipeline_stations.json"
LIVE_STATIONS_OUT = OUTPUT_DIR / "live_station_list.json"
LIVE_MAPPING_AUDIT_OUT = OUTPUT_DIR / "live_station_mapping_audit.csv"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


def normalize_station_id(value: object) -> str:
    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text.zfill(11) if text.isdigit() and len(text) < 11 else text


def split_isd_station_id(station_id: str) -> tuple[str, str]:
    normalized = normalize_station_id(station_id)

    if len(normalized) >= 11:
        return normalized[:6], normalized[6:11]

    return normalized[:6], ""


def normalize_icao(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip().upper()

    if text in {"", "NAN", "NONE", "NULL", "9999", "99999", "-9999"}:
        return None

    if len(text) == 4 and text[0].isalpha():
        return text

    return None


def clean_text(value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, float) and math.isnan(value):
        return ""

    return str(value).strip()


def build_all_pipeline_stations(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = [
        "station_id",
        "latitude",
        "longitude",
        "state",
        "avg_wind_speed_ms",
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {SOURCE_CSV}: {missing}")

    stations = (
        df[required_cols]
        .dropna(subset=["station_id", "latitude", "longitude", "state"])
        .drop_duplicates(subset=["station_id"])
        .copy()
    )

    stations["station_id"] = stations["station_id"].map(normalize_station_id)
    stations["state"] = stations["state"].astype(str).str.strip().str.upper()

    stations["USAF"] = stations["station_id"].map(lambda x: split_isd_station_id(x)[0])
    stations["WBAN"] = stations["station_id"].map(lambda x: split_isd_station_id(x)[1])

    stations = stations.sort_values(["state", "station_id"])

    return stations


def pipeline_records_from_df(stations: pd.DataFrame) -> list[dict]:
    records = []

    for row in stations.itertuples(index=False):
        records.append(
            {
                "station_id": str(row.station_id),
                "usaf": str(row.USAF),
                "wban": str(row.WBAN),
                "state": str(row.state),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "avg_wind_speed_ms": float(row.avg_wind_speed_ms),
                "live_observation_available": False,
                "source": "pipeline_station_map_export",
            }
        )

    return records


def load_isd_history() -> pd.DataFrame:
    if not ISD_HISTORY_CSV.exists():
        raise FileNotFoundError(f"Missing {ISD_HISTORY_CSV}")

    history = pd.read_csv(ISD_HISTORY_CSV, dtype=str)

    required_cols = ["USAF", "WBAN", "ICAO", "LAT", "LON", "BEGIN", "END"]
    missing = [col for col in required_cols if col not in history.columns]
    if missing:
        raise ValueError(f"{ISD_HISTORY_CSV} missing required columns: {missing}")

    history["USAF"] = history["USAF"].astype(str).str.strip()
    history["WBAN"] = history["WBAN"].astype(str).str.strip()
    history["ICAO_CLEAN"] = history["ICAO"].map(normalize_icao)

    if "NAME" not in history.columns:
        history["NAME"] = ""

    return history


def build_live_stations_from_isd_mapping(stations: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    history = load_isd_history()

    merged = stations.merge(
        history,
        on=["USAF", "WBAN"],
        how="left",
        suffixes=("_pipeline", "_history"),
    )

    merged["has_icao"] = merged["ICAO_CLEAN"].notna()

    candidates = merged[merged["has_icao"]].copy()

    candidates["END_SORT"] = pd.to_numeric(candidates["END"], errors="coerce").fillna(0)
    candidates["avg_wind_speed_ms"] = pd.to_numeric(
        candidates["avg_wind_speed_ms"], errors="coerce"
    ).fillna(0)

    candidates = candidates.sort_values(
        ["ICAO_CLEAN", "END_SORT", "avg_wind_speed_ms"],
        ascending=[True, False, False],
    ).drop_duplicates(subset=["ICAO_CLEAN"])

    live_records = []

    for row in candidates.itertuples(index=False):
        name = clean_text(getattr(row, "NAME", ""))

        lat = getattr(row, "latitude", None)
        lon = getattr(row, "longitude", None)

        if pd.isna(lat):
            lat = getattr(row, "LAT", None)

        if pd.isna(lon):
            lon = getattr(row, "LON", None)

        live_records.append(
            {
                "station_id": str(row.ICAO_CLEAN),
                "nws_station_id": str(row.ICAO_CLEAN),
                "isd_station_id": str(row.station_id),
                "usaf": str(row.USAF),
                "wban": str(row.WBAN),
                "name": name,
                "city": name,
                "state": str(row.state),
                "latitude": float(lat),
                "longitude": float(lon),
                "avg_wind_speed_ms": float(row.avg_wind_speed_ms),
                "live_observation_available": True,
                "live_api_verified": False,
                "source": "isd_history_icao_mapping",
            }
        )

    audit_cols = [
        "station_id",
        "USAF",
        "WBAN",
        "state",
        "latitude",
        "longitude",
        "avg_wind_speed_ms",
        "ICAO",
        "ICAO_CLEAN",
        "has_icao",
        "NAME",
        "BEGIN",
        "END",
    ]
    audit_cols = [col for col in audit_cols if col in merged.columns]

    return live_records, merged[audit_cols].copy()


def main() -> None:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(
            f"{SOURCE_CSV} does not exist. Run scripts/export_website_artifacts.py first."
        )

    df = pd.read_csv(SOURCE_CSV)

    pipeline_stations_df = build_all_pipeline_stations(df)
    all_pipeline_stations = pipeline_records_from_df(pipeline_stations_df)

    live_stations, audit = build_live_stations_from_isd_mapping(pipeline_stations_df)

    write_json(ALL_PIPELINE_STATIONS_OUT, all_pipeline_stations)
    write_json(LIVE_STATIONS_OUT, live_stations)

    audit.to_csv(LIVE_MAPPING_AUDIT_OUT, index=False)
    print(f"Wrote {LIVE_MAPPING_AUDIT_OUT}")

    print("\nStation artifact summary:")
    print(f"Pipeline stations: {len(all_pipeline_stations)}")
    print(f"Pipeline states: {pipeline_stations_df['state'].nunique()}")
    print(f"Live-enabled ICAO/NWS candidate stations: {len(live_stations)}")

    if live_stations:
        by_state = pd.Series([station["state"] for station in live_stations]).value_counts()
        print("\nLive-enabled candidate stations by state:")
        print(by_state.sort_index().to_string())


if __name__ == "__main__":
    main()