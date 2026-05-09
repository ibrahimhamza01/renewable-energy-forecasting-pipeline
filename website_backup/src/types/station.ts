export type LiveStation = {
  station_id: string;
  name: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
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