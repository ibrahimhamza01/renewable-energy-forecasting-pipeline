"use client";

import { useMemo, useState } from "react";
import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

type Row = Record<string, string | number>;

type PipelineSummary = {
    historical_window: {
        start_year: number;
        end_year: number;
    };
    coverage: {
        states: number;
        daily_region_rows: number;
        station_daily_rows: number;
        top_station_export_rows: number;
    };
};

type Props = {
    pipelineSummary: PipelineSummary;
    stateSummaryRows: Row[];
    yearlyRows: Row[];
    monthlyRows: Row[];
    topStationRows: Row[];
    stationMetadataRows: Row[];
};

function asNumber(value: unknown, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function fmt(value: number, digits = 3) {
    return value.toFixed(digits);
}

function percent(value: number, digits = 1) {
    return `${(value * 100).toFixed(digits)}%`;
}

function monthLabel(month: string | number) {
    const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const index = Number(month) - 1;
    return labels[index] ?? String(month);
}

function getString(row: Row | undefined, keys: string[], fallback = "") {
    if (!row) return fallback;

    for (const key of keys) {
        const value = row[key];
        if (value !== undefined && value !== null && String(value).trim() !== "") {
            return String(value);
        }
    }

    return fallback;
}

function getStationId(row: Row) {
    return getString(row, ["station_id", "STATION", "station", "usaf_wban"]);
}

function tooltipNumber(value: unknown) {
    return asNumber(value);
}

function capacityTooltip(value: unknown) {
    return [percent(tooltipNumber(value)), "Capacity Factor"];
}

function avgCapacityTooltip(value: unknown) {
    return [percent(tooltipNumber(value)), "Avg Capacity Factor"];
}

function windSpeedTooltip(value: unknown) {
    return [`${fmt(tooltipNumber(value), 2)} m/s`, "Avg Wind Speed"];
}

function hasCoordinate(value: number) {
    return Number.isFinite(value) && value !== 0;
}

export default function WindResultsExplorer({
    pipelineSummary,
    stateSummaryRows,
    yearlyRows,
    monthlyRows,
    topStationRows,
    stationMetadataRows,
}: Props) {
    const states = useMemo(
        () =>
            Array.from(new Set(stateSummaryRows.map((row) => String(row.state))))
                .filter(Boolean)
                .sort(),
        [stateSummaryRows],
    );

    const years = useMemo(
        () =>
            Array.from(new Set(yearlyRows.map((row) => String(row.year))))
                .filter(Boolean)
                .sort(),
        [yearlyRows],
    );

    const [selectedState, setSelectedState] = useState("TX");
    const [selectedYear, setSelectedYear] = useState("2023");

    const stationMetadataById = useMemo(() => {
        const map = new Map<string, Row>();

        stationMetadataRows.forEach((row) => {
            const id = getStationId(row);
            if (id) map.set(id, row);
        });

        return map;
    }, [stationMetadataRows]);

    const selectedStateSummary = useMemo(() => {
        return stateSummaryRows.find((row) => String(row.state) === selectedState);
    }, [stateSummaryRows, selectedState]);

    const stateRanking = useMemo(() => {
        return [...stateSummaryRows]
            .map((row) => ({
                state: String(row.state),
                avg_capacity_factor: asNumber(row.avg_capacity_factor),
                avg_wind_speed_ms: asNumber(row.avg_wind_speed_ms),
                day_count: asNumber(row.day_count),
            }))
            .sort((a, b) => b.avg_capacity_factor - a.avg_capacity_factor)
            .slice(0, 10);
    }, [stateSummaryRows]);

    const yearlyTrend = useMemo(() => {
        return yearlyRows
            .filter((row) => String(row.state) === selectedState)
            .map((row) => ({
                year: String(row.year),
                avg_capacity_factor: asNumber(row.avg_capacity_factor),
                avg_wind_speed_ms: asNumber(row.avg_wind_speed_ms),
            }))
            .sort((a, b) => Number(a.year) - Number(b.year));
    }, [yearlyRows, selectedState]);

    const monthlyProfile = useMemo(() => {
        return monthlyRows
            .filter((row) => String(row.state) === selectedState)
            .filter((row) => String(row.year) === selectedYear)
            .map((row) => ({
                month: monthLabel(row.month),
                month_number: asNumber(row.month),
                capacity_factor: asNumber(row.capacity_factor),
            }))
            .sort((a, b) => a.month_number - b.month_number);
    }, [monthlyRows, selectedState, selectedYear]);

    const topStations = useMemo(() => {
        return topStationRows
            .filter((row) => String(row.state) === selectedState)
            .map((row) => {
                const stationId = String(row.station_id);
                const metadata = stationMetadataById.get(stationId);

                return {
                    station_id: stationId,
                    station_label: `${selectedState} weather site ${stationId.slice(-4)}`,
                    state: String(row.state),
                    avg_wind_speed_ms: asNumber(row.avg_wind_speed_ms),
                    avg_capacity_factor: asNumber(row.avg_capacity_factor),
                };
            })
            .sort((a, b) => b.avg_wind_speed_ms - a.avg_wind_speed_ms)
            .slice(0, 10);
    }, [topStationRows, selectedState, stationMetadataById]);

    return (
        <section className="space-y-8">
            <div className="grid gap-4 md:grid-cols-4">
                <Metric
                    label="Historical Window"
                    value={`${pipelineSummary.historical_window.start_year}–${pipelineSummary.historical_window.end_year}`}
                    helper="Full NOAA ISD period preserved in website artifacts."
                />
                <Metric
                    label="State Coverage"
                    value={`${pipelineSummary.coverage.states} states`}
                    helper="Contiguous U.S. states represented after pipeline filtering."
                />
                <Metric
                    label="Daily Region Rows"
                    value={pipelineSummary.coverage.daily_region_rows.toLocaleString()}
                    helper="State-day historical wind records used for trends."
                />
                <Metric
                    label="Station Daily Rows"
                    value={pipelineSummary.coverage.station_daily_rows.toLocaleString()}
                    helper="Station-day records behind station summaries."
                />
            </div>

            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-5">
                <h2 className="text-lg font-semibold text-cyan-100">
                    How to read the wind potential score
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                    Capacity factor is a normalized wind-potential score from{" "}
                    <span className="font-semibold text-white">0 to 1</span>. Higher is
                    better. A value like <span className="font-semibold text-white">0.05</span>{" "}
                    means the historical wind resource averaged about 5% of rated potential
                    for that period. These values are conservative because they are derived
                    from NOAA weather observations and a simplified turbine-inspired power
                    curve, not measured turbine production.
                </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h2 className="text-2xl font-semibold text-white">
                    Interactive Historical Wind Explorer
                </h2>
                <p className="mt-2 max-w-4xl text-sm text-slate-400">
                    Choose a state and year to inspect monthly wind behavior, long-run wind
                    trends, and the strongest processed weather stations.
                </p>

                <div className="mt-6 grid gap-4 md:grid-cols-2">
                    <label className="text-sm text-slate-300">
                        State
                        <select
                            value={selectedState}
                            onChange={(event) => setSelectedState(event.target.value)}
                            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                        >
                            {states.map((state) => (
                                <option key={state} value={state}>
                                    {state}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label className="text-sm text-slate-300">
                        Year
                        <select
                            value={selectedYear}
                            onChange={(event) => setSelectedYear(event.target.value)}
                            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                        >
                            {years.map((year) => (
                                <option key={year} value={year}>
                                    {year}
                                </option>
                            ))}
                        </select>
                    </label>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Metric
                    label={`${selectedState} Avg Capacity Factor`}
                    value={percent(asNumber(selectedStateSummary?.avg_capacity_factor))}
                    helper="Long-run average wind-potential score. Higher means stronger resource."
                />
                <Metric
                    label={`${selectedState} Avg Wind Speed`}
                    value={`${fmt(asNumber(selectedStateSummary?.avg_wind_speed_ms), 2)} m/s`}
                    helper="Average regional wind speed in meters per second."
                />
                <Metric
                    label={`${selectedState} Daily Records`}
                    value={asNumber(selectedStateSummary?.day_count).toLocaleString()}
                    helper="Number of state-day records behind this state's summary."
                />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Monthly Wind Profile — {selectedState}, {selectedYear}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                    Changing the year updates this monthly profile. Peaks show months where
                    historical wind potential was strongest for the selected state.
                </p>

                <div className="mt-6 h-[420px]">
                    <ResponsiveContainer>
                        <AreaChart data={monthlyProfile}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="month" stroke="#94a3b8" />
                            <YAxis
                                stroke="#94a3b8"
                                tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
                            />
                            <Tooltip formatter={capacityTooltip} />
                            <Legend />
                            <Area
                                type="monotone"
                                dataKey="capacity_factor"
                                name="Capacity Factor"
                                stroke="#22d3ee"
                                fill="#0e7490"
                                fillOpacity={0.35}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    31-Year Wind Potential Trend — {selectedState}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                    This compares long-run annual wind potential with average wind speed.
                    It helps show whether a state has stable resource strength or large
                    year-to-year variation.
                </p>

                <div className="mt-6 h-[520px]">
                    <ResponsiveContainer>
                        <ComposedChart data={yearlyTrend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="year" stroke="#94a3b8" />
                            <YAxis
                                yAxisId="left"
                                stroke="#94a3b8"
                                tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
                            />
                            <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" />
                            <Tooltip
                                formatter={(value, name) => {
                                    const label = String(name);
                                    if (label.includes("Capacity")) {
                                        return [percent(tooltipNumber(value)), label];
                                    }
                                    return [`${fmt(tooltipNumber(value), 2)} m/s`, label];
                                }}
                            />
                            <Legend />
                            <Bar
                                yAxisId="left"
                                dataKey="avg_capacity_factor"
                                name="Avg Capacity Factor"
                                fill="#0e7490"
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="avg_wind_speed_ms"
                                name="Avg Wind Speed m/s"
                                stroke="#38bdf8"
                                strokeWidth={3}
                                dot={false}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Strongest Long-Run Wind Resource States
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                    This chart compares which states consistently showed the strongest
                    historical wind resource across 31 years of NOAA observations. Higher
                    values indicate stronger long-run wind potential.
                </p>

                <div className="mt-6 h-[460px]">
                    <ResponsiveContainer>
                        <BarChart data={stateRanking} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                type="number"
                                stroke="#94a3b8"
                                tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
                            />
                            <YAxis
                                dataKey="state"
                                type="category"
                                stroke="#94a3b8"
                                width={50}
                                interval={0}
                            />
                            <Tooltip formatter={avgCapacityTooltip} />
                            <Legend />
                            <Bar
                                dataKey="avg_capacity_factor"
                                name="Avg Capacity Factor"
                                fill="#38bdf8"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Highest-Wind Weather Stations — {selectedState}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                    These are the strongest processed NOAA weather stations in the selected
                    state. Station coordinates are included when metadata exists in the
                    historical pipeline exports.
                </p>

                <div className="mt-6 h-[420px]">
                    <ResponsiveContainer>
                        <BarChart data={topStations} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" stroke="#94a3b8" />
                            <YAxis
                                dataKey="station_label"
                                type="category"
                                stroke="#94a3b8"
                                width={180}
                                interval={0}
                            />
                            <Tooltip formatter={windSpeedTooltip} />
                            <Legend />
                            <Bar
                                dataKey="avg_wind_speed_ms"
                                name="Avg Wind Speed"
                                fill="#38bdf8"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800">
                    <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="bg-slate-900">
                            <tr>
                                <th className="px-4 py-3 text-left text-slate-300">Rank</th>
                                <th className="px-4 py-3 text-left text-slate-300">Weather Site</th>
                                <th className="px-4 py-3 text-left text-slate-300">Avg Wind Speed</th>
                                <th className="px-4 py-3 text-left text-slate-300">Wind Potential</th>
                                <th className="px-4 py-3 text-left text-slate-300">Pipeline ID</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {topStations.map((station, index) => (
                                <tr key={station.station_id}>
                                    <td className="px-4 py-3 text-slate-400">{index + 1}</td>
                                    <td className="px-4 py-3 text-slate-300">{station.station_label}</td>
                                    <td className="px-4 py-3 text-cyan-300">
                                        {fmt(station.avg_wind_speed_ms, 2)} m/s
                                    </td>
                                    <td className="px-4 py-3 text-slate-400">
                                        {percent(station.avg_capacity_factor)}
                                    </td>
                                    <td className="px-4 py-3 text-slate-500">{station.station_id}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}

function Metric({
    label,
    value,
    helper,
}: {
    label: string;
    value: string;
    helper?: string;
}) {
    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{value}</p>
            {helper ? (
                <p className="mt-2 text-xs leading-5 text-slate-500">{helper}</p>
            ) : null}
        </div>
    );
}