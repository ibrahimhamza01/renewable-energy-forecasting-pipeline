const pipelineStages = [
  {
    step: "01",
    title: "Raw NOAA ISD",
    subtitle: "AWS Open Data",
    text: "Hourly station-year CSV files are discovered from NOAA ISD. The raw dataset is global, wide, sparse, and encoded.",
    output: "station-year CSV inputs",
  },
  {
    step: "02",
    title: "Bronze",
    subtitle: "Raw ingestion",
    text: "Spark reads many NOAA files in parallel and writes normalized raw Parquet outputs to reduce small-file overhead.",
    output: "bronze/isd",
  },
  {
    step: "03",
    title: "Silver",
    subtitle: "Parsing + cleaning",
    text: "Encoded fields like WND, TMP, DEW, VIS, CIG, and SLP are parsed, quality-controlled, standardized, and enriched with station metadata.",
    output: "silver/weather",
  },
  {
    step: "04",
    title: "Gold",
    subtitle: "Wind analytics",
    text: "Clean observations are converted into turbine-inspired wind potential metrics and aggregated into station, state, and regional tables.",
    output: "gold/wind",
  },
  {
    step: "05",
    title: "Feature Engineering",
    subtitle: "Forecast table",
    text: "Lag, rolling, temporal, regional, and long-run state features are assembled into an ML-ready forecasting table.",
    output: "gold/wind/ml/base",
  },
  {
    step: "06",
    title: "Spark ML",
    subtitle: "Historical forecasting",
    text: "Spark MLlib models are trained and evaluated using time-based splits. The final tuned GBT predicts next-day regional capacity factor.",
    output: "final_tuned_gbt",
  },
  {
    step: "07",
    title: "Artifacts",
    subtitle: "Website preservation",
    text: "Forecasts, metrics, station lists, trends, benchmark results, and figures are exported as lightweight CSV/JSON/image files.",
    output: "website/public/data",
  },
  {
    step: "08",
    title: "Website + API",
    subtitle: "Portable product",
    text: "Next.js dashboards and FastAPI live analysis consume preserved artifacts and live NOAA observations without needing Spark at runtime.",
    output: "/live, /results, /forecasting",
  },
];

const architectureCards = [
  {
    title: "Heavy processing layer",
    items: [
      "PySpark ETL",
      "NOAA ISD parsing",
      "quality control",
      "gold table generation",
      "feature engineering",
      "Spark MLlib training",
    ],
  },
  {
    title: "Portable product layer",
    items: [
      "Next.js website",
      "FastAPI live analysis service",
      "CSV/JSON artifacts",
      "static figures",
      "verified station lists",
      "NOAA/NWS live observations",
    ],
  },
  {
    title: "What survives without EC2/S3",
    items: [
      "historical dashboards",
      "forecasting diagnostics",
      "benchmark dashboards",
      "live station explorer",
      "live wind outlook",
      "model metrics and interpretation",
    ],
  },
];

const proofArtifacts = [
  ["Processed stations", "2,419"],
  ["Verified live stations", "1,981"],
  ["Forecast evaluation rows", "535,961"],
  ["Historical window", "1995–2025"],
  ["State coverage", "48 states"],
  ["Final model", "Spark MLlib GBT"],
];

export default function PipelinePage() {
  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-10">
      <section className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900">
        <div className="border-b border-slate-800 bg-slate-950/60 p-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            Pipeline Architecture
          </p>

          <h1 className="mt-3 max-w-4xl text-4xl font-bold tracking-tight text-white md:text-5xl">
            From 600GB+ NOAA weather observations to a deployable live wind
            analytics platform.
          </h1>

          <p className="mt-5 max-w-4xl text-base leading-7 text-slate-300">
            The system separates large-scale historical processing from
            lightweight deployment. Spark and Airflow build trusted analytical
            and ML artifacts; the website and FastAPI backend consume those
            artifacts for dashboards, forecasting diagnostics, and live wind
            outlooks.
          </p>
        </div>

        <div className="grid gap-px bg-slate-800 md:grid-cols-3">
          {proofArtifacts.map(([label, value]) => (
            <div key={label} className="bg-slate-900 p-6">
              <p className="text-sm text-slate-400">{label}</p>
              <p className="mt-2 text-2xl font-bold text-white">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
              End-to-end flow
            </p>
            <h2 className="mt-2 text-3xl font-bold text-white">
              Data lake → ML pipeline → preserved artifacts → live product
            </h2>
          </div>

          <p className="max-w-xl text-sm leading-6 text-slate-400">
            Each stage produces a concrete output that feeds the next layer. The
            final website remains usable even when the distributed cloud
            environment is unavailable.
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {pipelineStages.map((stage, index) => (
            <div
              key={stage.step}
              className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-950 p-5 md:grid-cols-[80px_240px_1fr_220px]"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cyan-400 font-bold text-slate-950">
                {stage.step}
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white">
                  {stage.title}
                </h3>
                <p className="text-sm text-cyan-300">{stage.subtitle}</p>
              </div>

              <p className="text-sm leading-6 text-slate-400">{stage.text}</p>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Output
                </p>
                <p className="mt-1 break-words text-sm font-medium text-slate-200">
                  {stage.output}
                </p>
              </div>

              {index < pipelineStages.length - 1 ? (
                <div className="hidden md:col-span-4 md:block">
                  <div className="ml-6 h-4 border-l border-dashed border-cyan-700" />
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-3">
        {architectureCards.map((card) => (
          <div
            key={card.title}
            className="rounded-3xl border border-slate-800 bg-slate-900 p-6"
          >
            <h2 className="text-xl font-semibold text-white">{card.title}</h2>

            <ul className="mt-5 space-y-3 text-sm text-slate-400">
              {card.items.map((item) => (
                <li key={item} className="flex gap-3">
                  <span className="mt-2 h-1.5 w-1.5 rounded-full bg-cyan-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            Historical ML path
          </p>

          <h2 className="mt-2 text-2xl font-bold text-white">
            Spark model training and evaluation
          </h2>

          <p className="mt-4 text-sm leading-7 text-slate-400">
            The forecasting model is trained offline using Spark MLlib on a
            time-based split. Its predictions are exported into
            forecast-vs-actual artifacts so the website can show honest holdout
            evaluation without requiring a live Spark cluster.
          </p>

          <div className="mt-5 rounded-2xl bg-slate-950 p-4 text-sm text-slate-300">
            NOAA history → Spark features → final_tuned_gbt → forecast outputs →
            website diagnostics
          </div>
        </div>

        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            Live product path
          </p>

          <h2 className="mt-2 text-2xl font-bold text-white">
            NOAA-powered live wind outlook
          </h2>

          <p className="mt-4 text-sm leading-7 text-slate-400">
            The live service does not pretend to serve the Spark model. It
            fetches current NOAA observations, computes a turbine-inspired
            capacity factor, compares against preserved historical state
            summaries, and returns a deployable next-24-hour outlook.
          </p>

          <div className="mt-5 rounded-2xl bg-slate-950 p-4 text-sm text-slate-300">
            NOAA live API → FastAPI service → power curve → historical context →
            live outlook
          </div>
        </div>
      </section>
    </main>
  );
}