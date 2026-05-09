import MapPanel from "@/components/MapPanel";
import WindResultsExplorer from "@/components/WindResultsExplorer";
import { loadCsv } from "@/lib/csv";

type CsvRow = Record<string, string>;

function numericRows(rows: CsvRow[]) {
  return rows.map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([key, value]) => {
        const num = Number(value);
        return [key, Number.isFinite(num) && value !== "" ? num : value];
      }),
    ),
  );
}

export default async function ResultsPage() {
  const regionalRaw = await loadCsv<CsvRow>("/data/regional_trends.csv");
  const seasonalRaw = await loadCsv<CsvRow>("/data/seasonal_trends.csv");
  const stationRaw = await loadCsv<CsvRow>("/data/us_wind_station_map.csv");

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-8">
        <header>
          <p className="text-sm font-medium uppercase tracking-wide text-cyan-400">
            Historical Pipeline Results
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-white">
            Wind Potential Results Dashboard
          </h1>
          <p className="mt-4 max-w-3xl text-slate-400">
            Explore preserved Spark pipeline outputs using filters for state,
            year, and season. This page connects the static map artifact with
            interactive analytical results from the historical wind pipeline.
          </p>
        </header>

        <MapPanel
          title="U.S. Wind Potential Map"
          description="Station-level average wind speed exported from the historical Spark analytics pipeline."
          imageSrc="/assets/us_wind_potential_map.png"
        />

        <WindResultsExplorer
          regionalRows={numericRows(regionalRaw)}
          seasonalRows={numericRows(seasonalRaw)}
          stationRows={numericRows(stationRaw)}
        />
      </div>
    </main>
  );
}