"use client";

import { useState } from "react";
import {
  analyzeLiveWindOutlook,
  type LiveWindOutlookResponse,
} from "@/lib/modelServiceClient";

type Props = {
  defaultStationId?: string;
};

function pct(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

function num(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return value.toFixed(digits);
}

function labelText(label: string): string {
  return label.replaceAll("_", " ");
}

export default function LiveWindOutlook({ defaultStationId = "KMSP" }: Props) {
  const [stationId, setStationId] = useState(defaultStationId);
  const [result, setResult] = useState<LiveWindOutlookResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    setLoading(true);
    setError("");

    try {
      const data = await analyzeLiveWindOutlook(stationId.trim().toUpperCase());
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Unable to fetch outlook.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-700 bg-slate-900/70 p-6 shadow-lg">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          Portable Backend Service
        </p>
        <h2 className="mt-2 text-2xl font-bold text-white">
          Live Wind Outlook
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-300">
          This service calls live NOAA/NWS observations, converts wind speed into
          estimated capacity factor, compares current conditions against
          preserved Spark pipeline artifacts, and returns a next-24-hour outlook
          range. It does not retrain or serve the Spark MLlib model.
        </p>
        <div className="mt-4 rounded-xl border border-slate-700 bg-slate-950/60 p-4 text-xs text-slate-400">
          <p>
            Live NOAA observations + turbine-inspired power curve + preserved Spark
            pipeline artifacts.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          value={stationId}
          onChange={(event) => setStationId(event.target.value)}
          placeholder="KMSP"
          className="w-full rounded-xl border border-slate-600 bg-slate-950 px-4 py-3 text-white outline-none focus:border-cyan-400 sm:max-w-xs"
        />

        <button
          onClick={handleAnalyze}
          disabled={loading || !stationId.trim()}
          className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Analyzing..." : "Analyze live outlook"}
        </button>
      </div>

      {error && (
        <div className="mt-5 rounded-xl border border-red-500/40 bg-red-950/40 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-5">
          <div className="grid gap-4 md:grid-cols-4">
            <Metric
              label="Live wind speed"
              value={`${num(result.live.wind_speed_ms)} m/s`}
            />
            <div>
              <Metric
                label="Current capacity factor"
                value={pct(result.live.current_capacity_factor)}
              />

              {result.live.current_capacity_factor === 0 && (
                <p className="mt-2 text-xs text-slate-400">
                  Below turbine cut-in threshold.
                </p>
              )}
            </div>
            <Metric
              label="State baseline CF"
              value={pct(result.historical_context.state_long_run_avg_cf)}
            />
            <Metric
              label="24h center estimate"
              value={pct(result.next_24h_outlook.center_estimate)}
            />
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-5">
            <h3 className="text-lg font-semibold text-white">
              {result.station_name ?? result.station_id} · {result.state}
            </h3>

            <p className="mt-2 text-sm text-slate-300">
              {result.historical_context.summary}
            </p>

            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <Detail
                label="Condition"
                value={labelText(result.historical_context.condition_label)}
              />
              <Detail
                label="24h outlook range"
                value={`${pct(
                  result.next_24h_outlook.estimated_capacity_factor_range[0]
                )} – ${pct(
                  result.next_24h_outlook.estimated_capacity_factor_range[1]
                )}`}
              />
              <Detail
                label="Tendency"
                value={labelText(result.next_24h_outlook.tendency)}
              />
              <Detail
                label="Wind direction"
                value={`${num(result.live.wind_direction_deg, 0)}°`}
              />
              <Detail
                label="Temperature"
                value={`${num(result.live.temperature_c)} °C`}
              />
              <Detail
                label="Observation age"
                value={`${num(result.observation_age_minutes)} min`}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-5">
            <h3 className="text-lg font-semibold text-white">
              Historical model context
            </h3>

            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <Detail
                label="Model"
                value={result.model_context.historical_model_name}
              />
              <Detail
                label="RMSE"
                value={result.model_context.historical_rmse.toFixed(4)}
              />
              <Detail
                label="MAE"
                value={result.model_context.historical_mae.toFixed(4)}
              />
            </div>

            <p className="mt-4 text-sm text-slate-400">
              {result.model_context.note}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-950 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-200">{value}</p>
    </div>
  );
}
