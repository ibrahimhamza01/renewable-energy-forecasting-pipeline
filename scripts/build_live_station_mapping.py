from pathlib import Path
import json
import math

import pandas as pd


PIPELINE_STATIONS_JSON = Path("website/public/data/all_pipeline_stations.json")
ISD_HISTORY_CSV = Path("data/raw/noaa_metadata/isd-history.csv")

OUTPUT_DIR = Path("website/public/data")
OUTPUT_JSON = OUTPUT_DIR / "live_station_list.json"
MAPPING_AUDIT_CSV = OUTPUT_DIR / "live_station_mapping_audit.csv"


def normalize_station_id(value: object) -> str:
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def split_isd_station_id(station_id: str) -> tuple[str, str]:
    station_id = normalize_station_id(station_id)

    # Most ISD station IDs in this project are USAF(6) + WBAN(5)
    if len(station_id) >= 11:
        return station_id[:6], station_id[6:11]

    return station_id[:6], ""


def normalize_icao(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip().upper()

    if not text:
        return None

    if text in {"NAN", "NONE", "NULL", "9999", "99999", "-9999"}:
        return None

    # NWS station IDs are commonly ICAO-style 4-character codes like KSFO.
    if len(text) == 4 and text[0].isalpha():
        return text

    return None


def load_pipeline_stations() -> pd.DataFrame:
    if not PIPELINE_STATIONS_JSON.exists():
        raise FileNotFoundError(f"Missing {PIPELINE_STATIONS_JSON}")

    with PIPELINE_STATIONS_JSON.open("r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.DataFrame(records)

    if "station_id" not in df.columns:
        raise ValueError("all_pipeline_stations.json missing station_id")

    df["station_id"] = df["station_id"].map(normalize_station_id)

    split_cols = df["station_id"].map(split_isd_station_id)
    df["USAF"] = split_cols.map(lambda x: x[0])
    df["WBAN"] = split_cols.map(lambda x: x[1])

    return df


def load_isd_history() -> pd.DataFrame:
    if not ISD_HISTORY_CSV.exists():
        raise FileNotFoundError(f"Missing {ISD_HISTORY_CSV}")

    df = pd.read_csv(ISD_HISTORY_CSV, dtype=str)

    required = ["USAF", "WBAN", "ST", "ICAO", "LAT", "LON", "BEGIN", "END"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"isd-history.csv missing columns: {missing}")

    df["USAF"] = df["USAF"].astype(str).str.strip()
    df["WBAN"] = df["WBAN"].astype(str).str.strip()
    df["ST"] = df["ST"].astype(str).str.strip()
    df["ICAO_CLEAN"] = df["ICAO"].map(normalize_icao)

    return df


def build_mapping() -> tuple[list[dict], pd.DataFrame]:
    pipeline = load_pipeline_stations()
    history = load_isd_history()

    merged = pipeline.merge(
        history,
        on=["USAF", "WBAN"],
        how="left",
        suffixes=("_pipeline", "_history"),
    )

    # Keep only stations that have an ICAO/NWS-style code.
    live_candidates = merged[merged["ICAO_CLEAN"].notna()].copy()

    # Keep US stations only where possible.
    if "state" in live_candidates.columns:
        live_candidates = live_candidates[
            live_candidates["state"].notna()
            & (live_candidates["state"].astype(str).str.len() == 2)
        ]

    # Deduplicate by live station code. Prefer higher avg wind and latest END.
    live_candidates["avg_wind_speed_ms"] = pd.to_numeric(
        live_candidates["avg_wind_speed_ms"], errors="coerce"
    ).fillna(0)

    live_candidates["END_SORT"] = pd.to_numeric(
        live_candidates["END"], errors="coerce"
    ).fillna(0)

    live_candidates = live_candidates.sort_values(
        ["ICAO_CLEAN", "END_SORT", "avg_wind_speed_ms"],
        ascending=[True, False, False],
    )

    live_candidates = live_candidates.drop_duplicates(subset=["ICAO_CLEAN"])

    live_records = []

    for row in live_candidates.itertuples(index=False):
        # Prefer pipeline coordinates because they come from your processed station map.
        lat = getattr(row, "latitude", None)
        lon = getattr(row, "longitude", None)

        if pd.isna(lat) or pd.isna(lon):
            lat = getattr(row, "LAT", None)
            lon = getattr(row, "LON", None)

        live_records.append(
            {
                "station_id": row.ICAO_CLEAN,
                "nws_station_id": row.ICAO_CLEAN,
                "isd_station_id": row.station_id,
                "usaf": row.USAF,
                "wban": row.WBAN,
                "name": str(getattr(row, "NAME", "")).strip(),
                "city": str(getattr(row, "NAME", "")).strip(),
                "state": str(getattr(row, "state", "")).strip(),
                "latitude": float(lat),
                "longitude": float(lon),
                "avg_wind_speed_ms": float(row.avg_wind_speed_ms),
                "live_observation_available": True,
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
        "NAME",
        "BEGIN",
        "END",
    ]

    existing_audit_cols = [c for c in audit_cols if c in merged.columns]
    audit = merged[existing_audit_cols].copy()

    return live_records, audit


def main() -> None:
    live_records, audit = build_mapping()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_JSON.write_text(
        json.dumps(live_records, indent=2),
        encoding="utf-8",
    )

    audit.to_csv(MAPPING_AUDIT_CSV, index=False)

    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {MAPPING_AUDIT_CSV}")
    print(f"Live-enabled mapped stations: {len(live_records)}")

    by_state = pd.Series([r["state"] for r in live_records]).value_counts()
    print("\nLive-enabled stations by state:")
    print(by_state.sort_index().to_string())


if __name__ == "__main__":
    main()