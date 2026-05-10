"use client";

import { useMemo, useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

type Row = Record<string, string | number>;

type FeatureImportance = {
    feature: string;
    importance: number;
    signed_correlation?: number;
    method?: string;
};

type Props = {
    forecastRows: Row[];
    featureImportanceRows: FeatureImportance[];
};

function asNumber(value: unknown, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function percent(value: number, digits = 1) {
    return `${(value * 100).toFixed(digits)}%`;
}

function readableFeatureName(name: string) {
    return name
        .replaceAll("_", " ")
        .replaceAll("cf", "capacity factor")
        .replaceAll("ms", "m/s")
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function downsample<T>(rows: T[], maxPoints = 450) {
    if (rows.length <= maxPoints) return rows;

    const step = Math.ceil(rows.length / maxPoints);
    return rows.filter((_, index) => index % step === 0);
}

export default function ForecastChart({
    forecastRows,
    featureImportanceRows,
}: Props) {
    const states = useMemo(
        () =>
            Array.from(new Set(forecastRows.map((row) => String(row.state))))
                .filter(Boolean)
                .sort(),
        [forecastRows],
    );

    const years = useMemo(
        () =>
            Array.from(new Set(forecastRows.map((row) => String(row.year))))
                .filter(Boolean)
                .sort(),
        [forecastRows],
    );

    const [selectedState, setSelectedState] = useState("TX");
    const [selectedYear, setSelectedYear] = useState("2023");

    const filteredRows = useMemo(() => {
        return forecastRows
            .filter((row) => String(row.state) === selectedState)
            .filter((row) => String(row.year) === selectedYear)
            .map((row) => ({
                date: String(row.date),
                actual: asNumber(row.actual),
                prediction: asNumber(row.prediction),
                error: asNumber(row.error),
                absolute_error: asNumber(row.absolute_error),
                mean_region_wind_speed_ms: asNumber(row.mean_region_wind_speed_ms),
            }))
            .sort((a, b) => a.date.localeCompare(b.date));
    }, [forecastRows, selectedState, selectedYear]);

    const chartRows = useMemo(() => downsample(filteredRows), [filteredRows]);
    const sampleRows = filteredRows.slice(0, 12);

    const featureRows = useMemo(() => {
        return featureImportanceRows
            .slice(0, 12)
            .map((row) => ({
                feature: readableFeatureName(row.feature),
                importance: asNumber(row.importance),
            }))
            .sort((a, b) => b.importance - a.importance);
    }, [featureImportanceRows]);

    const avgAbsoluteError = useMemo(() => {
        if (!filteredRows.length) return 0;
        return (
            filteredRows.reduce((sum, row) => sum + row.absolute_error, 0) /
            filteredRows.length
        );
    }, [filteredRows]);

    return (
        <section className="space-y-8">
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h2 className="text-2xl font-semibold text-white">
                    Forecast vs Actual Explorer
                </h2>

                <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
                    Select a holdout state and year to inspect how closely the final tuned
                    GBT model followed actual next-day wind potential.
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
                        Holdout Year
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
                <MiniStat
                    label={`${selectedState} ${selectedYear} Rows`}
                    value={filteredRows.length.toLocaleString()}
                    helper="State-day forecasts available for this selection."
                />
                <MiniStat
                    label="Selection MAE"
                    value={percent(avgAbsoluteError, 2)}
                    helper="Average absolute error for the selected state and year."
                />
                <MiniStat
                    label="Forecast Type"
                    value="Historical holdout"
                    helper="Used for evaluation because actual outcomes are known."
                />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Forecast vs Actual — {selectedState}, {selectedYear}
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                    Capacity factor is shown as a percentage. The closer the prediction line
                    stays to the actual line, the better the model performed for that period.
                    Sudden spikes are the hardest events to forecast.
                </p>

                <div className="mt-6 h-[520px]">
                    <ResponsiveContainer>
                        <LineChart data={chartRows}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="date" stroke="#94a3b8" minTickGap={40} />
                            <YAxis
                                stroke="#94a3b8"
                                tickFormatter={(value) => percent(Number(value), 0)}
                            />
                            <Tooltip
                                formatter={(value, name) => [
                                    percent(asNumber(value), 2),
                                    String(name),
                                ]}
                            />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="actual"
                                name="Actual"
                                stroke="#38bdf8"
                                strokeWidth={2}
                                dot={false}
                            />
                            <Line
                                type="monotone"
                                dataKey="prediction"
                                name="Prediction"
                                stroke="#22c55e"
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Model Feature Importance
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                    These features explain what the model relied on most. Wind speed, wind
                    variability, and rolling historical capacity-factor features carry most
                    of the signal.
                </p>

                <div className="mt-6 h-[460px]">
                    <ResponsiveContainer>
                        <BarChart data={featureRows} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" stroke="#94a3b8" />
                            <YAxis
                                dataKey="feature"
                                type="category"
                                stroke="#94a3b8"
                                width={270}
                                interval={0}
                            />
                            <Tooltip
                                formatter={(value) => [
                                    asNumber(value).toFixed(3),
                                    "Importance",
                                ]}
                            />
                            <Legend />
                            <Bar dataKey="importance" name="Importance" fill="#38bdf8" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                <h3 className="text-xl font-semibold text-white">
                    Sample Predictions — {selectedState}, {selectedYear}
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                    A row-level preview of actual next-day wind potential, model prediction,
                    and absolute error.
                </p>

                <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800">
                    <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="bg-slate-900">
                            <tr>
                                <th className="px-4 py-3 text-left text-slate-300">Date</th>
                                <th className="px-4 py-3 text-left text-slate-300">Actual</th>
                                <th className="px-4 py-3 text-left text-slate-300">
                                    Prediction
                                </th>
                                <th className="px-4 py-3 text-left text-slate-300">
                                    Absolute Error
                                </th>
                                <th className="px-4 py-3 text-left text-slate-300">
                                    Avg Wind Speed
                                </th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-slate-800">
                            {sampleRows.map((row) => (
                                <tr key={row.date}>
                                    <td className="px-4 py-3 text-slate-300">{row.date}</td>
                                    <td className="px-4 py-3 text-cyan-300">
                                        {percent(row.actual, 2)}
                                    </td>
                                    <td className="px-4 py-3 text-green-300">
                                        {percent(row.prediction, 2)}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400">
                                        {percent(row.absolute_error, 2)}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400">
                                        {row.mean_region_wind_speed_ms.toFixed(2)} m/s
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

function MiniStat({
    label,
    value,
    helper,
}: {
    label: string;
    value: string;
    helper: string;
}) {
    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{value}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">{helper}</p>
        </div>
    );
}