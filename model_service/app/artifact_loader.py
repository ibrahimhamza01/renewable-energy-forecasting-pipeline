from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@lru_cache
def load_stations() -> list[dict]:
    path = DATA_DIR / "verified_live_station_list.json"

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ["stations", "data", "items"]:
            if key in data and isinstance(data[key], list):
                return data[key]

    if isinstance(data, list):
        return data

    return []


@lru_cache
def load_state_summary() -> pd.DataFrame:
    path = DATA_DIR / "state_wind_summary.csv"
    return pd.read_csv(path)


@lru_cache
def load_top_stations() -> pd.DataFrame:
    path = DATA_DIR / "top_wind_stations.csv"
    return pd.read_csv(path)


@lru_cache
def load_model_metrics() -> dict:
    path = DATA_DIR / "model_metrics.json"

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_station(station_id: str) -> dict | None:
    station_id = station_id.upper().strip()

    for station in load_stations():
        possible_ids = [
            station.get("station_id"),
            station.get("id"),
            station.get("icao"),
            station.get("nws_station_id"),
            station.get("live_station_id"),
        ]

        normalized_ids = {str(x).upper() for x in possible_ids if x}

        if station_id in normalized_ids:
            return station

    return None


def get_state_context(state: str) -> dict:
    state = state.upper().strip()
    df = load_state_summary()

    state_col = _first_existing_column(df, ["state", "STATE"])
    if not state_col:
        return {}

    row = df[df[state_col].astype(str).str.upper() == state]

    if row.empty:
        return {}

    record = row.iloc[0].to_dict()

    avg_cf_col = _first_existing_key(
        record,
        [
            "state_long_run_avg_cf",
            "avg_capacity_factor",
            "mean_capacity_factor",
            "daily_region_capacity_factor",
            "long_run_avg_cf",
        ],
    )

    avg_wind_col = _first_existing_key(
        record,
        [
            "avg_wind_speed_ms",
            "state_long_run_avg_wind_speed_ms",
            "mean_wind_speed_ms",
            "long_run_avg_wind_speed_ms",
        ],
    )

    vol_col = _first_existing_key(
        record,
        [
            "state_long_run_volatility",
            "capacity_factor_std",
            "std_capacity_factor",
            "long_run_volatility",
        ],
    )

    return {
        "state": state,
        "state_long_run_avg_cf": _safe_float(record.get(avg_cf_col)) if avg_cf_col else None,
        "state_long_run_avg_wind_speed_ms": _safe_float(record.get(avg_wind_col)) if avg_wind_col else None,
        "state_long_run_volatility": _safe_float(record.get(vol_col)) if vol_col else None,
        "raw": record,
    }


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _first_existing_key(record: dict, candidates: list[str]) -> str | None:
    for key in candidates:
        if key in record:
            return key
    return None


def _safe_float(value) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None