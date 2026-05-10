import ForecastChart from "@/components/ForecastChart";
import MetricCard from "@/components/MetricCard";
import { loadCsv } from "@/lib/csv";
import { readFile } from "fs/promises";
import path from "path";

type CsvRow = Record<string, string>;

type ModelMetrics = {
    final_model_name: string;
    model_family: string;
    target: string;
    metrics: {
        rmse: number;
        mae: number;
        bias: number;
        evaluation_rows: number;
    };
    coverage: {
        start_date: string;
        end_date: string;
        states: number;
    };
};

type FeatureImportance = {
    feature: string;
    importance: number;
    signed_correlation?: number;
    method?: string;
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

function percent(value: number, digits = 2) {
    return `${(value * 100).toFixed(digits)}%`;
}

export default async function ForecastingPage() {
    const [forecastRaw, modelMetrics, featureImportance] = await Promise.all([
        loadCsv<CsvRow>("/data/forecast_vs_actual.csv"),
        loadJson<ModelMetrics>("/data/model_metrics.json"),
        loadJson<FeatureImportance[]>("/data/feature_importance.json"),
    ]);

    const forecastRows = numericRows(forecastRaw).filter((row) => {
        const year = Number(row.year);
        return year >= 2023;
    });

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
            <div className="mx-auto max-w-7xl space-y-8">
                <header>
                    <p className="text-sm font-medium uppercase tracking-wide text-cyan-400">
                        Forecasting Model Results
                    </p>

                    <h1 className="mt-3 text-4xl font-bold tracking-tight text-white">
                        ML Wind Forecasting Dashboard
                    </h1>

                    <p className="mt-4 max-w-3xl text-slate-400">
                        This page shows historical holdout forecasts from the final Spark ML
                        model. It compares predicted next-day wind potential against actual
                        observed outcomes so the model can be evaluated honestly.
                    </p>
                </header>

                <div className="grid gap-4 md:grid-cols-4">
                    <MetricCard
                        label="Final Model"
                        value={modelMetrics.final_model_name}
                        helper={modelMetrics.model_family}
                    />
                    <MetricCard
                        label="RMSE"
                        value={percent(modelMetrics.metrics.rmse)}
                        helper="Root mean squared forecast error. Lower is better."
                    />
                    <MetricCard
                        label="MAE"
                        value={percent(modelMetrics.metrics.mae)}
                        helper="Average absolute forecast error. Lower is better."
                    />
                    <MetricCard
                        label="Bias"
                        value={percent(modelMetrics.metrics.bias)}
                        helper="Average prediction minus actual. Near zero is best."
                    />
                </div>

                <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-5">
                    <h2 className="text-lg font-semibold text-cyan-100">
                        Forecast evaluation scope
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                        The selectable years are 2023–2025 because this page shows historical
                        holdout evaluation, not live future forecasting. Actual outcomes are
                        already known for these dates, so RMSE, MAE, and bias can be measured.
                        Future-date operational forecasting belongs in the next inference-service
                        layer.
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                    <MetricCard
                        label="Evaluation Rows"
                        value={modelMetrics.metrics.evaluation_rows.toLocaleString()}
                        helper="Forecast rows joined with actual next-day outcomes."
                    />
                    <MetricCard
                        label="Coverage"
                        value={`${modelMetrics.coverage.states} states`}
                        helper={`${modelMetrics.coverage.start_date} to ${modelMetrics.coverage.end_date}`}
                    />
                    <MetricCard
                        label="Target"
                        value="Next-day capacity factor"
                        helper={modelMetrics.target}
                    />
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                    <h2 className="text-lg font-semibold text-white">
                        Model interpretation
                    </h2>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
                        <li>
                            • The model tracks normal wind-potential movement reasonably well.
                        </li>
                        <li>
                            • The largest errors happen during sudden wind spikes, which are hard
                            to predict from historical daily features.
                        </li>
                        <li>
                            • The near-zero bias means the model is not consistently overpredicting
                            or underpredicting.
                        </li>
                        <li>
                            • Wind speed and rolling capacity-factor features dominate the signal.
                        </li>
                    </ul>
                </div>

                <ForecastChart
                    forecastRows={forecastRows}
                    featureImportanceRows={featureImportance}
                />
            </div>
        </main>
    );
}