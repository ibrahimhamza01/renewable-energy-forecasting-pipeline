from __future__ import annotations

from model_service.app.artifact_loader import (
    find_station,
    get_state_context,
    load_model_metrics,
)
from model_service.app.power_curve import estimate_capacity_factor


def analyze_live_observation(observation: dict) -> dict:
    station_id = observation["station_id"]
    station = find_station(station_id) or {}

    station_name = (
        station.get("name")
        or station.get("city")
        or station.get("station_name")
        or f"Station {station_id}"
    )

    state = (
        station.get("state")
        or station.get("STATE")
        or observation.get("state")
        or "UNKNOWN"
    )

    wind_speed_ms = observation.get("wind_speed_ms")
    current_cf = estimate_capacity_factor(wind_speed_ms)

    state_context = get_state_context(state) if state != "UNKNOWN" else {}
    avg_cf = state_context.get("state_long_run_avg_cf")
    avg_wind_speed_ms = state_context.get("state_long_run_avg_wind_speed_ms")
    volatility = state_context.get("state_long_run_volatility")

    condition_label = classify_condition(current_cf, avg_cf, volatility)
    outlook = estimate_24h_outlook(current_cf, avg_cf, volatility)
    metrics = load_model_metrics()

    return {
        "station_id": station_id,
        "station_name": station_name,
        "state": state,
        "timestamp": observation.get("timestamp"),
        "observation_age_minutes": observation.get("observation_age_minutes"),
        "live": {
            "wind_speed_ms": wind_speed_ms,
            "wind_direction_deg": observation.get("wind_direction_deg"),
            "temperature_c": observation.get("temperature_c"),
            "current_capacity_factor": current_cf,
        },
        "historical_context": {
            "state_long_run_avg_cf": avg_cf,
            "state_long_run_avg_wind_speed_ms": avg_wind_speed_ms,
            "state_long_run_volatility": volatility,
            "condition_label": condition_label,
            "summary": build_context_sentence(
                state=state,
                current_cf=current_cf,
                avg_cf=avg_cf,
                avg_wind_speed_ms=avg_wind_speed_ms,
                live_wind_speed_ms=wind_speed_ms,
                label=condition_label,
            ),
        },
        "next_24h_outlook": outlook,
        "model_context": {
            "historical_model_name": metrics.get("final_model_name"),
            "model_family": metrics.get("model_family"),
            "target": metrics.get("target"),
            "historical_rmse": metrics.get("metrics", {}).get("rmse"),
            "historical_mae": metrics.get("metrics", {}).get("mae"),
            "historical_bias": metrics.get("metrics", {}).get("bias"),
            "note": (
                "The live outlook is not serving the Spark MLlib model. "
                "It uses live NOAA observations, power-curve logic, and "
                "preserved historical artifacts."
            ),
        },
    }


def classify_condition(
    current_cf: float,
    avg_cf: float | None,
    volatility: float | None,
) -> str:
    if avg_cf is None:
        if current_cf >= 0.5:
            return "strong_live_wind"
        if current_cf >= 0.15:
            return "moderate_live_wind"
        return "low_live_wind"

    band = volatility if volatility and volatility > 0 else 0.05

    if current_cf >= avg_cf + band:
        return "above_normal"
    if current_cf <= avg_cf - band:
        return "below_normal"

    return "near_normal"


def estimate_24h_outlook(
    current_cf: float,
    avg_cf: float | None,
    volatility: float | None,
) -> dict:
    baseline = avg_cf if avg_cf is not None else current_cf
    vol = volatility if volatility and volatility > 0 else 0.05

    center = 0.65 * current_cf + 0.35 * baseline
    lower = max(0.0, center - vol)
    upper = min(1.0, center + vol)

    if current_cf > baseline + vol:
        tendency = "above_normal_possible_reversion"
        confidence = "moderate"
    elif current_cf < baseline - vol:
        tendency = "below_normal_possible_recovery"
        confidence = "moderate"
    else:
        tendency = "stable_near_normal"
        confidence = "moderate"

    return {
        "horizon": "next_24_hours",
        "estimated_capacity_factor_range": [round(lower, 4), round(upper, 4)],
        "center_estimate": round(center, 4),
        "tendency": tendency,
        "confidence": confidence,
        "method": (
            "Heuristic outlook from live capacity factor, historical state average, "
            "and long-run volatility. No model retraining."
        ),
    }


def build_context_sentence(
    state: str,
    current_cf: float,
    avg_cf: float | None,
    avg_wind_speed_ms: float | None,
    live_wind_speed_ms: float | None,
    label: str,
) -> str:
    cf_pct = round(current_cf * 100, 1)

    if avg_cf is None:
        return (
            f"Current estimated wind potential is {cf_pct}%. "
            "Historical state capacity-factor baseline was not available."
        )

    avg_cf_pct = round(avg_cf * 100, 1)

    wind_phrase = ""
    if live_wind_speed_ms is not None and avg_wind_speed_ms is not None:
        wind_phrase = (
            f" Live wind speed is {round(live_wind_speed_ms, 1)} m/s versus "
            f"a long-run {state} average of {round(avg_wind_speed_ms, 1)} m/s."
        )

    if label == "above_normal":
        return (
            f"Current estimated wind potential is {cf_pct}%, above the long-run "
            f"{state} baseline of {avg_cf_pct}%."
            f"{wind_phrase}"
        )

    if label == "below_normal":
        return (
            f"Current estimated wind potential is {cf_pct}%, below the long-run "
            f"{state} baseline of {avg_cf_pct}%."
            f"{wind_phrase}"
        )

    return (
        f"Current estimated wind potential is {cf_pct}%, near the long-run "
        f"{state} baseline of {avg_cf_pct}%."
        f"{wind_phrase}"
    )