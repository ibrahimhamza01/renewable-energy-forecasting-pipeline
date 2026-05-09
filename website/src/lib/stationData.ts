import type { LiveStation, PipelineStation } from "@/types/station";

export async function loadVerifiedLiveStations(): Promise<LiveStation[]> {
  const response = await fetch("/data/verified_live_station_list.json", {
    cache: "force-cache",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to load verified live stations: ${response.status} ${response.statusText}`
    );
  }

  return (await response.json()) as LiveStation[];
}

export async function loadAllPipelineStations(): Promise<PipelineStation[]> {
  const response = await fetch("/data/all_pipeline_stations.json", {
    cache: "force-cache",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to load pipeline stations: ${response.status} ${response.statusText}`
    );
  }

  return (await response.json()) as PipelineStation[];
}

export function filterLiveStationsByState(
  stations: LiveStation[],
  state: string
): LiveStation[] {
  if (!state || state === "ALL") {
    return stations;
  }

  return stations.filter((station) => station.state === state);
}

export function getAvailableStates<T extends { state: string }>(
  stations: T[]
): string[] {
  return Array.from(new Set(stations.map((station) => station.state))).sort();
}

export function searchLiveStations(
  stations: LiveStation[],
  query: string
): LiveStation[] {
  const normalizedQuery = query.trim().toLowerCase();

  if (!normalizedQuery) {
    return stations;
  }

  return stations.filter((station) => {
    const searchable = [
      station.station_id,
      station.nws_station_id,
      station.isd_station_id,
      station.name,
      station.city,
      station.state,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return searchable.includes(normalizedQuery);
  });
}

export function sortLiveStations(stations: LiveStation[]): LiveStation[] {
  return [...stations].sort((a, b) => {
    if (a.state !== b.state) {
      return a.state.localeCompare(b.state);
    }

    return a.station_id.localeCompare(b.station_id);
  });
}