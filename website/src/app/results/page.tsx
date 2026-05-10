import MapPanel from "@/components/MapPanel";
import WindResultsExplorer from "@/components/WindResultsExplorer";
import { loadCsv } from "@/lib/csv";
import { readFile } from "fs/promises";
import path from "path";

type CsvRow = Record<string, string>;

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

async function loadJson<T>(publicPath: string): Promise<T> {
    const cleanPath = publicPath.replace(/^\/+/, "");
    const filePath = path.join(process.cwd(), "public", cleanPath);
    const text = await readFile(filePath, "utf-8");
    return JSON.parse(text) as T;
}

export default async function ResultsPage() {
    const [
        pipelineSummary,
        stateSummaryRaw,
        yearlyRaw,
        monthlyRaw,
        topStationsRaw,
        stationMetadataRaw,
    ] = await Promise.all([
        loadJson<PipelineSummary>("/data/pipeline_summary.json"),
        loadCsv<CsvRow>("/data/state_wind_summary.csv"),
        loadCsv<CsvRow>("/data/yearly_state_summary.csv"),
        loadCsv<CsvRow>("/data/monthly_state_trends.csv"),
        loadCsv<CsvRow>("/data/top_wind_stations.csv"),
        loadCsv<CsvRow>("/data/us_wind_station_map.csv"),
    ]);

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
                        Explore full 1995–2025 Spark gold outputs across 48 contiguous U.S.
                        states. This dashboard turns preserved pipeline artifacts into
                        interactive historical wind analytics.
                    </p>
                </header>

                <MapPanel
                    title="U.S. Wind Potential Map"
                    description="Station-level average wind speed exported from the historical Spark analytics pipeline."
                    imageSrc="/assets/us_wind_potential_map.png"
                />

                <WindResultsExplorer
                    pipelineSummary={pipelineSummary}
                    stateSummaryRows={numericRows(stateSummaryRaw)}
                    yearlyRows={numericRows(yearlyRaw)}
                    monthlyRows={numericRows(monthlyRaw)}
                    topStationRows={numericRows(topStationsRaw)}
                    stationMetadataRows={numericRows(stationMetadataRaw)}
                />
            </div>
        </main>
    );
}