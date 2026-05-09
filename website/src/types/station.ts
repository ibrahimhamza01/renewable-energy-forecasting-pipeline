export type PipelineStation = {
  station_id: string;
  usaf?: string;
  wban?: string;
  state: string;
  latitude: number;
  longitude: number;
  avg_wind_speed_ms: number;
  live_observation_available: boolean;
  source: string;
};

export type LiveStation = {
  station_id: string;
  nws_station_id: string;
  isd_station_id?: string;
  usaf?: string;
  wban?: string;
  name?: string;
  city?: string;
  state: string;
  latitude: number;
  longitude: number;
  avg_wind_speed_ms?: number;
  live_observation_available: boolean;
  live_api_verified?: boolean;
  live_api_status?: number | null;
  live_api_error?: string | null;
  source: string;
};

export type LiveObservation = {
  stationId: string;
  timestamp: string | null;
  windSpeedMs: number | null;
  windDirectionDeg: number | null;
  temperatureC: number | null;
  rawSource: "NOAA_NWS";
};

export type NoaaObservationResponse = {
  properties?: {
    timestamp?: string;
    windSpeed?: {
      value: number | null;
      unitCode?: string;
    };
    windDirection?: {
      value: number | null;
      unitCode?: string;
    };
    temperature?: {
      value: number | null;
      unitCode?: string;
    };
  };
};

export type LiveObservationStatus =
  | "idle"
  | "loading"
  | "success"
  | "error"
  | "fallback";

export type LiveWindExplorerState = {
  selectedStation: LiveStation | null;
  observation: LiveObservation | null;
  status: LiveObservationStatus;
  errorMessage: string | null;
};