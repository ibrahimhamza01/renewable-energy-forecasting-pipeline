"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchLatestObservation } from "@/lib/noaaClient";
import { estimateCapacityFactor, formatCapacityFactor } from "@/lib/powerCurve";
import {
    filterLiveStationsByState,
    getAvailableStates,
    loadVerifiedLiveStations,
    searchLiveStations,
    sortLiveStations,
} from "@/lib/stationData";
import type {
    LiveObservation,
    LiveObservationStatus,
    LiveStation,
} from "@/types/station";

import PowerCurveChart from "./PowerCurveChart";

const MAX_VISIBLE_STATIONS = 80;

function hasUsefulName(station: LiveStation): boolean {
    const name = station.name?.trim();
    return Boolean(name && name.toLowerCase() !== "nan");
}

function getStationName(station: LiveStation): string {
    return hasUsefulName(station)
        ? station.name!.trim()
        : `Station ${station.nws_station_id}`;
}

function formatBrowserLocalTimestamp(timestamp: string | null | undefined): string {
    if (!timestamp) return "N/A";

    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) return timestamp;

    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
    }).format(parsed);
}

function formatUtcTimestamp(timestamp: string | null | undefined): string {
    if (!timestamp) return "N/A";

    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) return timestamp;

    return parsed.toISOString().replace(".000Z", "Z");
}

function formatObservationAge(timestamp: string | null | undefined): string {
    if (!timestamp) return "N/A";

    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) return "N/A";

    const ageMs = Date.now() - parsed.getTime();
    const ageMinutes = Math.max(0, Math.round(ageMs / 60000));

    if (ageMinutes < 1) return "Less than 1 minute ago";
    if (ageMinutes === 1) return "1 minute ago";
    if (ageMinutes < 60) return `${ageMinutes} minutes ago`;

    const ageHours = Math.round(ageMinutes / 60);
    if (ageHours === 1) return "1 hour ago";

    return `${ageHours} hours ago`;
}

function getOperatingExplanation(
    windSpeedMs: number | null | undefined,
    capacityFactor: number | null
): string {
    if (windSpeedMs === null || windSpeedMs === undefined || capacityFactor === null) {
        return "Load a live observation to place the station on the curve.";
    }

    if (windSpeedMs < 3) {
        return "Below cut-in: wind is too weak for meaningful turbine output.";
    }

    if (windSpeedMs >= 25) {
        return "Above cut-out: turbine cuts out to protect equipment in extreme wind.";
    }

    if (windSpeedMs >= 12) {
        return "Rated region: turbine is estimated near full output.";
    }

    return "Ramp-up region: output increases quickly as wind speed rises.";
}

export default function LiveWindExplorer() {
    const [hasMounted, setHasMounted] = useState(false);
    const [stations, setStations] = useState<LiveStation[]>([]);
    const [selectedState, setSelectedState] = useState("ALL");
    const [stationQuery, setStationQuery] = useState("");
    const [selectedStationId, setSelectedStationId] = useState("");
    const [observation, setObservation] = useState<LiveObservation | null>(null);
    const [status, setStatus] = useState<LiveObservationStatus>("idle");
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        setHasMounted(true);
    }, []);

    useEffect(() => {
        async function loadStations() {
            try {
                const loaded = sortLiveStations(await loadVerifiedLiveStations()).sort(
                    (a, b) => Number(hasUsefulName(b)) - Number(hasUsefulName(a))
                );

                setStations(loaded);

                if (loaded.length > 0) {
                    const firstNamed = loaded.find(hasUsefulName) ?? loaded[0];
                    setSelectedStationId(firstNamed.nws_station_id);
                }
            } catch (error) {
                console.error(error);
                setStatus("error");
                setErrorMessage("Failed to load verified live stations.");
            }
        }

        if (hasMounted) {
            loadStations();
        }
    }, [hasMounted]);

    const states = useMemo(() => getAvailableStates(stations), [stations]);

    const filteredStations = useMemo(() => {
        const byState = filterLiveStationsByState(stations, selectedState);
        const searched = searchLiveStations(byState, stationQuery);

        return sortLiveStations(searched)
            .sort((a, b) => Number(hasUsefulName(b)) - Number(hasUsefulName(a)))
            .slice(0, MAX_VISIBLE_STATIONS);
    }, [stations, selectedState, stationQuery]);

    const selectedStation = useMemo(() => {
        return stations.find((station) => station.nws_station_id === selectedStationId) ?? null;
    }, [stations, selectedStationId]);

    const capacity = estimateCapacityFactor(observation?.windSpeedMs ?? null);

    function selectStation(station: LiveStation) {
        setSelectedStationId(station.nws_station_id);
        setStationQuery("");
        setObservation(null);
        setStatus("idle");
        setErrorMessage(null);
    }

    async function handleFetchObservation() {
        if (!selectedStation) {
            setStatus("error");
            setErrorMessage("Select a station first.");
            return;
        }

        setStatus("loading");
        setErrorMessage(null);

        try {
            const latest = await fetchLatestObservation(selectedStation.nws_station_id);
            setObservation(latest);
            setStatus("success");
        } catch (error) {
            console.error(error);
            setObservation(null);
            setStatus("fallback");
            setErrorMessage(
                "Live NOAA observation is unavailable for this station right now. Station metadata and historical wind context are still available."
            );
        }
    }

    if (!hasMounted) {
        return (
            <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">Loading verified station explorer...</p>
            </section>
        );
    }

    return (
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <div className="mb-6">
                <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
                    Station Explorer
                </p>

                <h2 className="mt-2 text-2xl font-bold text-white">
                    Live NOAA wind potential estimate
                </h2>

                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
                    Search a verified station, fetch the latest NOAA observation, and estimate
                    current wind potential using the project power-curve logic.
                </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-lg">
                    <div className="space-y-4">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-slate-300">
                                State filter
                            </label>

                            <select
                                value={selectedState}
                                onChange={(event) => {
                                    setSelectedState(event.target.value);
                                    setStationQuery("");
                                    setSelectedStationId("");
                                    setObservation(null);
                                    setStatus("idle");
                                }}
                                className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-white outline-none focus:border-cyan-400"
                            >
                                <option value="ALL">All states</option>
                                {states.map((state) => (
                                    <option key={state} value={state}>
                                        {state}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-slate-300">
                                Verified live station
                            </label>

                            <input
                                value={stationQuery}
                                onChange={(event) => {
                                    setStationQuery(event.target.value);
                                    setSelectedStationId("");
                                    setObservation(null);
                                    setStatus("idle");
                                }}
                                placeholder="Search station code, name, or state..."
                                className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-white outline-none placeholder:text-slate-500 focus:border-cyan-400"
                            />

                            <div className="mt-2 max-h-64 overflow-y-auto rounded-xl border border-slate-800 bg-slate-900">
                                {filteredStations.length === 0 && stationQuery.trim().length > 0 ? (
                                    <div className="px-3 py-3 text-sm text-slate-400">
                                        No matching stations.
                                    </div>
                                ) : (
                                    filteredStations.map((station) => (
                                        <button
                                            key={station.nws_station_id}
                                            type="button"
                                            onClick={() => selectStation(station)}
                                            className={`block w-full border-b border-slate-800 px-3 py-2 text-left text-sm transition last:border-b-0 hover:bg-slate-800 ${selectedStationId === station.nws_station_id
                                                    ? "bg-cyan-950/50 text-cyan-200"
                                                    : "text-slate-300"
                                                }`}
                                        >
                                            <span className="font-semibold">{station.nws_station_id}</span>
                                            <span className="text-slate-500"> · </span>
                                            <span>{getStationName(station)}</span>
                                            <span className="text-slate-500"> · {station.state}</span>
                                        </button>
                                    ))
                                )}
                            </div>

                            <p className="mt-2 text-xs text-slate-500">
                                {stationQuery.trim().length > 0
                                    ? `Showing ${filteredStations.length.toLocaleString()} matching stations from ${stations.length.toLocaleString()} verified live stations.`
                                    : `Showing top ${filteredStations.length.toLocaleString()} verified live stations.`}
                            </p>
                        </div>

                        <button
                            onClick={handleFetchObservation}
                            disabled={!selectedStation || status === "loading"}
                            className="w-full rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {status === "loading" ? "Fetching NOAA observation..." : "Fetch live observation"}
                        </button>

                        {errorMessage && (
                            <div className="rounded-xl border border-red-900 bg-red-950/50 p-3 text-sm text-red-200">
                                {errorMessage}
                            </div>
                        )}

                        {selectedStation && (
                            <div className="rounded-xl bg-slate-900 p-4 text-sm text-slate-300">
                                <p className="font-semibold text-white">
                                    {selectedStation.nws_station_id} · {getStationName(selectedStation)}
                                </p>

                                <p>
                                    {selectedStation.state} · {selectedStation.latitude.toFixed(3)},{" "}
                                    {selectedStation.longitude.toFixed(3)}
                                </p>

                                <p className="mt-2 text-slate-400">
                                    Pipeline station ID: {selectedStation.isd_station_id ?? "N/A"}
                                </p>

                                {selectedStation.avg_wind_speed_ms !== undefined && (
                                    <p className="text-slate-400">
                                        Historical avg wind speed:{" "}
                                        {selectedStation.avg_wind_speed_ms.toFixed(2)} m/s
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="grid gap-4 md:grid-cols-4">
                        <MetricCard
                            label="Live wind speed"
                            value={
                                observation?.windSpeedMs === null || observation?.windSpeedMs === undefined
                                    ? "N/A"
                                    : `${observation.windSpeedMs.toFixed(2)} m/s`
                            }
                            helper="NOAA observation"
                        />

                        <MetricCard
                            label="Wind direction"
                            value={
                                observation?.windDirectionDeg === null ||
                                    observation?.windDirectionDeg === undefined
                                    ? "N/A"
                                    : `${Math.round(observation.windDirectionDeg)}°`
                            }
                            helper="Clockwise from north"
                        />

                        <MetricCard
                            label="Temperature"
                            value={
                                observation?.temperatureC === null || observation?.temperatureC === undefined
                                    ? "N/A"
                                    : `${observation.temperatureC.toFixed(1)} °C`
                            }
                            helper="NOAA observation"
                        />

                        <MetricCard
                            label="Estimated capacity factor"
                            value={formatCapacityFactor(capacity.capacityFactor)}
                            helper={
                                capacity.capacityFactor === 0
                                    ? "Below turbine cut-in or above cut-out"
                                    : "Power curve estimate"
                            }
                        />
                    </div>

                    <PowerCurveChart windSpeedMs={observation?.windSpeedMs ?? null} />

                    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                        <h3 className="text-lg font-semibold text-white">How to read this</h3>

                        <p className="mt-3 text-sm leading-6 text-slate-300">
                            The curve shows estimated wind output by wind speed. Below 3 m/s,
                            output is 0%. From 3–12 m/s, output ramps up. From 12–25 m/s,
                            output is rated. Above 25 m/s, the turbine cuts out for protection.
                        </p>

                        <p className="mt-3 text-sm text-cyan-300">
                            Current status:{" "}
                            {getOperatingExplanation(observation?.windSpeedMs, capacity.capacityFactor)}
                        </p>
                    </div>

                    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                        <h3 className="text-lg font-semibold text-white">Observation metadata</h3>

                        <div className="mt-4 grid gap-2 text-sm text-slate-300 md:grid-cols-2">
                            <p>
                                Request status:{" "}
                                <span className={status === "fallback" ? "text-amber-300" : "text-white"}>
                                    {status === "fallback" ? "NOAA API unavailable" : status}
                                </span>
                            </p>

                            <p>
                                Source: <span className="text-white">{observation?.rawSource ?? "N/A"}</span>
                            </p>

                            <p>
                                Observation time in your timezone:{" "}
                                <span className="text-white">
                                    {formatBrowserLocalTimestamp(observation?.timestamp)}
                                </span>
                            </p>

                            <p>
                                Observation age:{" "}
                                <span className="text-white">
                                    {formatObservationAge(observation?.timestamp)}
                                </span>
                            </p>

                            <p>
                                Original NOAA UTC timestamp:{" "}
                                <span className="text-white">
                                    {formatUtcTimestamp(observation?.timestamp)}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}

function MetricCard({
    label,
    value,
    helper,
}: {
    label: string;
    value: string;
    helper: string;
}) {
    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-lg">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{value}</p>
            <p className="mt-1 text-xs text-slate-500">{helper}</p>
        </div>
    );
}