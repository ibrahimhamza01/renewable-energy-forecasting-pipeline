from pathlib import Path
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LIVE_STATIONS_IN = Path("website/public/data/live_station_list.json")
LIVE_STATIONS_OUT = Path("website/public/data/live_station_list.json")
VERIFIED_OUT = Path("website/public/data/verified_live_station_list.json")
AUDIT_OUT = Path("website/public/data/live_station_api_verification_audit.json")

NOAA_BASE_URL = "https://api.weather.gov"
USER_AGENT = "renewable-energy-forecasting-pipeline-website (portfolio project)"

# Keep this conservative so we do not hammer NOAA.
REQUEST_SLEEP_SECONDS = 0.15
TIMEOUT_SECONDS = 8


def load_stations() -> list[dict]:
    if not LIVE_STATIONS_IN.exists():
        raise FileNotFoundError(f"Missing {LIVE_STATIONS_IN}")

    return json.loads(LIVE_STATIONS_IN.read_text(encoding="utf-8"))


def fetch_latest_observation(station_id: str) -> tuple[bool, int | None, str | None]:
    url = f"{NOAA_BASE_URL}/stations/{station_id}/observations/latest"

    request = Request(
        url,
        headers={
            "Accept": "application/geo+json",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            return 200 <= status < 300, status, None

    except HTTPError as exc:
        return False, exc.code, str(exc)

    except URLError as exc:
        return False, None, str(exc.reason)

    except Exception as exc:
        return False, None, str(exc)


def main() -> None:
    stations = load_stations()

    verified = []
    audit = []

    total = len(stations)

    for idx, station in enumerate(stations, start=1):
        station_id = station["nws_station_id"]

        ok, status, error = fetch_latest_observation(station_id)

        updated = dict(station)
        updated["live_api_verified"] = ok
        updated["live_api_status"] = status
        updated["live_api_error"] = error

        audit.append(
            {
                "station_id": station_id,
                "state": station.get("state"),
                "ok": ok,
                "status": status,
                "error": error,
            }
        )

        if ok:
            verified.append(updated)

        if idx % 50 == 0 or idx == total:
            print(f"Checked {idx}/{total}. Verified so far: {len(verified)}")

        time.sleep(REQUEST_SLEEP_SECONDS)

    LIVE_STATIONS_OUT.write_text(json.dumps([dict(s, live_api_verified=False) for s in stations], indent=2), encoding="utf-8")
    VERIFIED_OUT.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    AUDIT_OUT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print("\nVerification complete.")
    print(f"Candidate stations: {len(stations)}")
    print(f"Verified live stations: {len(verified)}")
    print(f"Wrote {VERIFIED_OUT}")
    print(f"Wrote {AUDIT_OUT}")


if __name__ == "__main__":
    main()