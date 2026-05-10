import Link from "next/link";

const cards = [
  {
    title: "Live Wind Outlook",
    href: "/live",
    text: "Explore live NOAA observations, turbine-inspired power-curve estimates, and deployable backend wind outlook analysis.",
  },
  {
    title: "Pipeline Architecture",
    href: "/pipeline",
    text: "Review the Spark ETL pipeline, Airflow orchestration, feature engineering, ML workflow, and artifact preservation design.",
  },
  {
    title: "Historical Results",
    href: "/results",
    text: "Analyze long-run wind potential trends, state summaries, regional outputs, and historical Spark analytics.",
  },
  {
    title: "Forecasting Model",
    href: "/forecasting",
    text: "Inspect model metrics, holdout forecast evaluation, feature importance, and forecasting diagnostics.",
  },
  {
    title: "Benchmarking",
    href: "/benchmarking",
    text: "Compare Spark and DuckDB analytical execution performance across benchmark workloads.",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-12">
      <section className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-8 shadow-2xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          Portfolio-grade renewable energy platform
        </p>

        <h1 className="mt-4 max-w-5xl text-4xl font-bold tracking-tight text-white md:text-6xl">
          Wind energy forecasting from distributed Spark pipelines to live NOAA
          analysis.
        </h1>

        <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
          This project combines large-scale NOAA weather processing, PySpark
          ETL, turbine-inspired wind modeling, ML forecasting, Airflow
          orchestration, benchmarking, preserved website artifacts, and a
          deployable FastAPI live analysis backend.
        </p>

        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            href="/live"
            className="rounded-xl bg-cyan-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Open Live Outlook
          </Link>

          <Link
            href="/pipeline"
            className="rounded-xl border border-slate-700 px-6 py-3 font-semibold text-slate-200 transition hover:bg-slate-800"
          >
            View Architecture
          </Link>
        </div>
      </section>

      <section className="mt-10 grid gap-5 md:grid-cols-3">
        <MetricCard title="Historical Window" value="1995–2025" />
        <MetricCard title="Verified Live Stations" value="1,981" />
        <MetricCard title="Forecast Evaluation Rows" value="535,961" />
      </section>

      <section className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:border-cyan-400 hover:bg-slate-900/80"
          >
            <h2 className="text-2xl font-semibold text-white">
              {card.title}
            </h2>

            <p className="mt-4 text-sm leading-7 text-slate-400">
              {card.text}
            </p>
          </Link>
        ))}
      </section>

      <section className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8">
        <h2 className="text-3xl font-bold text-white">
          End-to-end forecasting workflow
        </h2>

        <div className="mt-8 overflow-x-auto">
          <div className="min-w-[1000px] rounded-2xl border border-slate-800 bg-slate-950 p-6">
            <div className="grid grid-cols-6 gap-4 text-center">
              {[
                "NOAA ISD",
                "Spark ETL",
                "Gold Tables",
                "ML Training",
                "Artifact Exports",
                "Website + API",
              ].map((step) => (
                <div
                  key={step}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-5 text-sm font-semibold text-white"
                >
                  {step}
                </div>
              ))}
            </div>

            <p className="mt-5 text-center text-sm text-slate-500">
              ingestion → cleaning → feature engineering → forecasting →
              preserved artifacts → live analysis
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function MetricCard({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <p className="text-sm text-slate-400">{title}</p>

      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
    </div>
  );
}