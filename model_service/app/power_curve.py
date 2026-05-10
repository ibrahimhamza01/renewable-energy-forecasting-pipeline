from __future__ import annotations


def estimate_capacity_factor(
    wind_speed_ms: float | None,
    cut_in_ms: float = 3.0,
    rated_ms: float = 12.0,
    cut_out_ms: float = 25.0,
) -> float:
    if wind_speed_ms is None:
        return 0.0

    v = max(float(wind_speed_ms), 0.0)

    if v < cut_in_ms:
        return 0.0

    if cut_in_ms <= v < rated_ms:
        cf = ((v - cut_in_ms) / (rated_ms - cut_in_ms)) ** 3
        return round(min(max(cf, 0.0), 1.0), 6)

    if rated_ms <= v <= cut_out_ms:
        return 1.0

    return 0.0
