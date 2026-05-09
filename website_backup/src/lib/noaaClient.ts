import type { LiveObservation, NoaaObservationResponse } from "../types/station";

const NOAA_API_BASE_URL = "https://api.weather.gov";

export class NoaaClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NoaaClientError";
  }
}

function normalizeNumber(value: unknown): number | null {
  if (typeof value !== "number") {
    return null;
  }

  if (!Number.isFinite(value)) {
    return null;
  }

  return value;
}

export async function fetchLatestObservation(
  stationId: string
): Promise<LiveObservation> {
  const normalizedStationId = stationId.trim().toUpperCase();

  if (!normalizedStationId) {
    throw new NoaaClientError("Station ID is required.");
  }

  const url = `${NOAA_API_BASE_URL}/stations/${normalizedStationId}/observations/latest`;

  const response = await fetch(url, {
    headers: {
      Accept: "application/geo+json",
      "User-Agent":
        "renewable-energy-forecasting-pipeline-website (portfolio project)",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new NoaaClientError(
      `NOAA request failed for ${normalizedStationId}: ${response.status} ${response.statusText}`
    );
  }

  const payload = (await response.json()) as NoaaObservationResponse;

  const properties = payload.properties;

  if (!properties) {
    throw new NoaaClientError(
      `NOAA response for ${normalizedStationId} did not include observation properties.`
    );
  }

  return {
    stationId: normalizedStationId,
    timestamp: properties.timestamp ?? null,
    windSpeedMs: normalizeNumber(properties.windSpeed?.value),
    windDirectionDeg: normalizeNumber(properties.windDirection?.value),
    temperatureC: normalizeNumber(properties.temperature?.value),
    rawSource: "NOAA_NWS",
  };
}