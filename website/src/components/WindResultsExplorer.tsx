"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
} from "recharts";

type Row = Record<string, string | number>;

type Props = {
  regionalRows: Row[];
  seasonalRows: Row[];
  stationRows: Row[];
};

function asNumber(value: unknown) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function getYear(row: Row) {
  const raw = String(row.date ?? row.year ?? "");
  const match = raw.match(/\d{4}/);
  return match ? match[0] : "Unknown";
}

function getMonth(row: Row) {
  const raw = String(row.date ?? "");
  const match = raw.match(/\d{4}-(\d{2})/);
  return match ? Number(match[1]) : null;
}

function seasonFromMonth(month: number | null) {
  if (!month) return "Unknown";
  if ([12, 1, 2].includes(month)) return "winter";
  if ([3, 4, 5].includes(month)) return "spring";
  if ([6, 7, 8].includes(month)) return "summer";
  return "fall";
}

function getSeason(row: Row) {
  const direct = String(row.season ?? row.Season ?? "");
  if (direct) return direct.toLowerCase();
  return seasonFromMonth(getMonth(row));
}

function getRegion(row: Row) {
  return String(row.region ?? row.state ?? row.State ?? "Unknown");
}

function getCapacityFactor(row: Row) {
  return (
    asNumber(row.capacity_factor) ??
    asNumber(row.avg_capacity_factor) ??
    asNumber(row.mean_capacity_factor) ??
    asNumber(row.daily_capacity_factor) ??
    0
  );
}

function getWindSpeed(row: Row) {
  return (
    asNumber(row.avg_wind_speed_ms) ??
    asNumber(row.mean_wind_speed_ms) ??
    asNumber(row.wind_speed_ms) ??
    0
  );
}

export default function WindResultsExplorer({
  regionalRows,
  seasonalRows,
  stationRows,
}: Props) {
  const chartRegions = useMemo(() => {
    return Array.from(new Set(regionalRows.map(getRegion)))
      .filter((x) => x && x !== "Unknown")
      .sort();
  }, [regionalRows]);

  const chartYears = useMemo(() => {
    return Array.from(new Set(regionalRows.map(getYear)))
      .filter((x) => x !== "Unknown")
      .sort();
  }, [regionalRows]);

  const chartSeasons = ["winter", "spring", "summer", "fall"];

  const [selectedRegion, setSelectedRegion] = useState("All");
  const [selectedYear, setSelectedYear] = useState("All");
  const [selectedSeason, setSelectedSeason] = useState("All");

  const filteredRegional = useMemo(() => {
    return regionalRows
      .filter((row) => selectedRegion === "All" || getRegion(row) === selectedRegion)
      .filter((row) => selectedYear === "All" || getYear(row) === selectedYear)
      .filter((row) => selectedSeason === "All" || getSeason(row) === selectedSeason)
      .map((row) => ({
        date: String(row.date ?? row.year ?? ""),
        region: getRegion(row),
        season: getSeason(row),
        capacity_factor: getCapacityFactor(row),
      }));
  }, [regionalRows, selectedRegion, selectedYear, selectedSeason]);

  const seasonalTrend = useMemo(() => {
    const grouped = new Map<string, { label: string; total: number; count: number }>();

    regionalRows
      .filter((row) => selectedRegion === "All" || getRegion(row) === selectedRegion)
      .filter((row) => selectedYear === "All" || getYear(row) === selectedYear)
      .forEach((row) => {
        const season = getSeason(row);
        if (season === "Unknown") return;

        const current = grouped.get(season) ?? {
          label: season,
          total: 0,
          count: 0,
        };

        current.total += getCapacityFactor(row);
        current.count += 1;
        grouped.set(season, current);
      });

    return chartSeasons
      .map((season) => grouped.get(season))
      .filter(Boolean)
      .map((row) => ({
        season: row!.label,
        avg_capacity_factor: row!.count ? row!.total / row!.count : 0,
      }));
  }, [regionalRows, selectedRegion, selectedYear]);

  const filteredStations = useMemo(() => {
    return stationRows
      .filter((row) => selectedRegion === "All" || getRegion(row) === selectedRegion)
      .map((row) => ({
        station_id: String(row.station_id ?? row.STATION ?? ""),
        state: getRegion(row),
        latitude: asNumber(row.latitude) ?? asNumber(row.LATITUDE) ?? 0,
        longitude: asNumber(row.longitude) ?? asNumber(row.LONGITUDE) ?? 0,
        avg_wind_speed_ms: getWindSpeed(row),
      }))
      .sort((a, b) => b.avg_wind_speed_ms - a.avg_wind_speed_ms);
  }, [stationRows, selectedRegion]);

  const topStations = filteredStations.slice(0, 10);
  const highestWind = topStations[0]?.avg_wind_speed_ms ?? 0;

  return (
    <section className="space-y-8">
      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
        <h2 className="text-2xl font-semibold text-white">
          Interactive Wind Results Explorer
        </h2>

        <p className="mt-2 max-w-4xl text-sm text-slate-400">
          Explore the exported historical wind artifacts by region, year, and
          season. The filters below are based only on values actually present in
          the website CSV files.
        </p>

        {chartYears.length < 31 && (
          <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
            Current exported regional trend data contains {chartYears.length} year
            groups: {chartYears.join(", ")}. To show the full 1995–2025 history,
            regenerate <code>regional_trends.csv</code> from the full pipeline output.
          </div>
        )}

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <label className="text-sm text-slate-300">
            Region / State in Chart Data
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
            >
              <option value="All">All available regions</option>
              {chartRegions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-300">
            Year
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
            >
              <option value="All">All available years</option>
              {chartYears.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-300">
            Season
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
            >
              <option value="All">All seasons</option>
              {chartSeasons.map((season) => (
                <option key={season} value={season}>
                  {season}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
          <p className="text-sm text-slate-400">Stations in View</p>
          <p className="mt-2 text-3xl font-bold text-white">{filteredStations.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
          <p className="text-sm text-slate-400">Chart Regions</p>
          <p className="mt-2 text-3xl font-bold text-white">{chartRegions.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
          <p className="text-sm text-slate-400">Years in Export</p>
          <p className="mt-2 text-3xl font-bold text-white">{chartYears.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
          <p className="text-sm text-slate-400">Highest Avg Wind</p>
          <p className="mt-2 text-3xl font-bold text-white">
            {highestWind.toFixed(2)} m/s
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
        <h3 className="text-xl font-semibold text-white">
          Daily Wind Potential Over Time
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Plotting capacity factor for{" "}
          <span className="text-cyan-300">{selectedRegion}</span>,{" "}
          <span className="text-cyan-300">{selectedYear}</span>,{" "}
          <span className="text-cyan-300">{selectedSeason}</span>.
        </p>

        {filteredRegional.length === 0 ? (
          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-8 text-slate-300">
            No rows exist for this filter combination in the current exported CSV.
          </div>
        ) : (
          <div className="mt-6 h-[560px]">
            <ResponsiveContainer>
              <LineChart data={filteredRegional}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" minTickGap={42} stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={[0, "auto"]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="capacity_factor"
                  name="Capacity Factor"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
        <h3 className="text-xl font-semibold text-white">
          Seasonal Capacity Factor Profile
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Average wind potential by season for the selected region and year.
        </p>

        {seasonalTrend.length === 0 ? (
          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-8 text-slate-300">
            No seasonal rows exist for this filter combination.
          </div>
        ) : (
          <div className="mt-6 h-[420px]">
            <ResponsiveContainer>
              <AreaChart data={seasonalTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="season" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={[0, "auto"]} />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="avg_capacity_factor"
                  name="Avg Capacity Factor"
                  stroke="#22d3ee"
                  fill="#0e7490"
                  fillOpacity={0.35}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
        <h3 className="text-xl font-semibold text-white">
          Highest-Wind Stations
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Top processed stations by long-run average wind speed for the selected region.
        </p>

        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-4 py-3 text-left text-slate-300">Rank</th>
                <th className="px-4 py-3 text-left text-slate-300">Station</th>
                <th className="px-4 py-3 text-left text-slate-300">Region</th>
                <th className="px-4 py-3 text-left text-slate-300">Latitude</th>
                <th className="px-4 py-3 text-left text-slate-300">Longitude</th>
                <th className="px-4 py-3 text-left text-slate-300">Avg Wind</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800">
              {topStations.map((station, index) => (
                <tr key={`${station.station_id}-${index}`}>
                  <td className="px-4 py-3 text-slate-400">{index + 1}</td>
                  <td className="px-4 py-3 text-slate-300">{station.station_id}</td>
                  <td className="px-4 py-3 text-slate-400">{station.state}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {station.latitude.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {station.longitude.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-cyan-300">
                    {station.avg_wind_speed_ms.toFixed(2)} m/s
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}