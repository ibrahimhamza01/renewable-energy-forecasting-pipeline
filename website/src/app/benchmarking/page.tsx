import BenchmarkChart from "@/components/BenchmarkChart";
import MetricCard from "@/components/MetricCard";
import { loadCsv } from "@/lib/csv";
import MapPanel from "@/components/MapPanel";

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

function asNumber(value: unknown, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function getEngine(row: Record<string, string | number>) {
    return String(row.engine ?? row.system ?? row.backend ?? row.execution_engine ?? "Unknown");
}

function getRuntime(row: Record<string, string | number>) {
    return Math.min(asNumber(row.duckdb), asNumber(row.spark));
}

export default async function BenchmarkingPage() {
    const rawRows = await loadCsv<CsvRow>("/data/benchmark_comparison.csv");
    const rows = numericRows(rawRows);

    const engines = ["DuckDB", "Spark"];
    const fastest = [...rows].sort((a, b) => getRuntime(a) - getRuntime(b))[0];

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
            <div className="mx-auto max-w-7xl space-y-8">
                <header>
                    <p className="text-sm font-medium uppercase tracking-wide text-cyan-400">
                        Benchmarking Results
                    </p>

                    <h1 className="mt-3 text-4xl font-bold tracking-tight text-white">
                        DuckDB vs Spark Benchmarking Dashboard
                    </h1>

                    <p className="mt-4 max-w-3xl text-slate-400">
                        This page compares single-node DuckDB execution with Spark execution
                        on equivalent analytical workloads. It explains where lightweight
                        local analytics are enough and where distributed processing becomes
                        justified.
                    </p>
                </header>

                <div className="grid gap-4 md:grid-cols-3">
                    <MetricCard
                        label="Engines Compared"
                        value={engines.join(" vs ")}
                        helper="Single-node analytical engine compared with distributed Spark."
                    />
                    <MetricCard
                        label="Benchmark Rows"
                        value={rows.length.toLocaleString()}
                        helper="Exported benchmark observations used in this dashboard."
                    />
                    <MetricCard
                        label="Fastest Observed Run"
                        value={`${getRuntime(fastest).toFixed(3)} sec`}
                        helper="Fastest runtime across DuckDB and Spark benchmark columns."
                    />
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                    <h2 className="text-xl font-semibold text-white">
                        Benchmark Summary
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-slate-400">
                        This benchmark compares DuckDB and Spark on equivalent analytical tasks.
                        The goal is not to prove Spark is always faster. The goal is to show the
                        tradeoff: DuckDB is excellent for compact local analytics, while Spark is
                        appropriate when the same workflow scales to partitioned, multi-year,
                        cloud-backed NOAA datasets.
                    </p>
                </div>

                <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-5">
                    <h2 className="text-lg font-semibold text-cyan-100">
                        Benchmark interpretation
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-slate-300">
                        DuckDB is expected to perform very well on smaller local analytical
                        workloads because it avoids distributed scheduling overhead. Spark
                        can look slower on small data, but it becomes valuable when the same
                        workload needs to scale across much larger NOAA partitions, multiple
                        years, many stations, or cloud storage.
                    </p>
                </div>

                <BenchmarkChart rows={rows} />
                <MapPanel
                    title="Benchmark Runtime by Task"
                    description="Exported benchmark visualization comparing DuckDB and Spark runtime across analytical workloads."
                    imageSrc="/assets/benchmark_runtime_by_task.png"
                />

                <MapPanel
                    title="Spark Runtime Relative to DuckDB"
                    description="Relative Spark runtime compared to DuckDB for the same benchmark tasks."
                    imageSrc="/assets/benchmark_runtime_ratio.png"
                />

                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
                    <h2 className="text-xl font-semibold text-white">
                        What this benchmark proves
                    </h2>

                    <div className="mt-4 grid gap-4 md:grid-cols-3">
                        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                            <h3 className="font-semibold text-white">DuckDB strength</h3>
                            <p className="mt-2 text-sm leading-6 text-slate-400">
                                Excellent for local, compact analytical workloads and fast
                                iteration on exported Parquet or CSV data.
                            </p>
                        </div>

                        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                            <h3 className="font-semibold text-white">Spark strength</h3>
                            <p className="mt-2 text-sm leading-6 text-slate-400">
                                Better fit for large distributed processing, S3-backed data
                                lakes, partitioned NOAA history, and full pipeline execution.
                            </p>
                        </div>

                        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                            <h3 className="font-semibold text-white">Project takeaway</h3>
                            <p className="mt-2 text-sm leading-6 text-slate-400">
                                The project uses both tools where they make sense: DuckDB for
                                lean local analysis and Spark for scalable pipeline workloads.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}