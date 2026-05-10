from __future__ import annotations

from datetime import datetime, timezone
import httpx


class NOAAClient:
    def __init__(self, user_agent: str = "wind-energy-forecasting-platform/1.0"):
        self.base_url = "https://api.weather.gov"
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/geo+json",
        }

    async def get_latest_observation(self, station_id: str) -> dict:
        station_id = station_id.upper().strip()
        url = f"{self.base_url}/stations/{station_id}/observations/latest"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            payload = response.json()

        props = payload.get("properties", {})

        wind_speed_ms = self._extract_value(props.get("windSpeed"))
        wind_direction_deg = self._extract_value(props.get("windDirection"))
        temperature_c = self._extract_value(props.get("temperature"))
        timestamp = props.get("timestamp")

        return {
            "station_id": station_id,
            "timestamp": timestamp,
            "wind_speed_ms": wind_speed_ms,
            "wind_direction_deg": wind_direction_deg,
            "temperature_c": temperature_c,
            "observation_age_minutes": self._age_minutes(timestamp),
            "raw_source": "NOAA/NWS latest observation",
        }

    @staticmethod
    def _extract_value(field: dict | None) -> float | None:
        if not isinstance(field, dict):
            return None
        value = field.get("value")
        return None if value is None else float(value)

    @staticmethod
    def _age_minutes(timestamp: str | None) -> float | None:
        if not timestamp:
            return None
        try:
            observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return round((now - observed).total_seconds() / 60.0, 1)
        except Exception:
            return None
