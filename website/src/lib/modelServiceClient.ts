export type LiveWindOutlookResponse = {
  station_id: string;
  station_name: string | null;
  state: string;
  timestamp: string | null;
  observation_age_minutes: number | null;
  live: {
    wind_speed_ms: number | null;
    wind_direction_deg: number | null;
    temperature_c: number | null;
    current_capacity_factor: number;
  };
  historical_context: {
    state_long_run_avg_cf: number | null;
    state_long_run_avg_wind_speed_ms: number | null;
    state_long_run_volatility: number | null;
    condition_label: string;
    summary: string;
  };
  next_24h_outlook: {
    horizon: string;
    estimated_capacity_factor_range: [number, number];
    center_estimate: number;
    tendency: string;
    confidence: string;
    method: string;
  };
  model_context: {
    historical_model_name: string;
    model_family: string;
    target: string;
    historical_rmse: number;
    historical_mae: number;
    historical_bias: number;
    note: string;
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_MODEL_API_URL ?? "http://127.0.0.1:8000";

export async function analyzeLiveWindOutlook(
  stationId: string
): Promise<LiveWindOutlookResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze-live`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ station_id: stationId }),
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorData = await response.json();

      if (typeof errorData?.detail === "string") {
        message = errorData.detail;
      }
    } catch {
      // ignore JSON parse failure
    }

    throw new Error(message);
  }

  return response.json();
}
