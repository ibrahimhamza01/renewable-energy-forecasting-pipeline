"use client";

import { useMemo } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

type Row = Record<string, string | number>;

type Props = {
    rows: Row[];
};

function asNumber(value: unknown, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function getTask(row: Row) {
    return String(row.task_name ?? row.task ?? row.benchmark ?? "Benchmark");
}

export default function BenchmarkChart({ rows }: Props) {
    const chartRows = useMemo(() => {
        return rows.map((row) => ({
            task: getTask(row),
            DuckDB: asNumber(row.duckdb),
            Spark: asNumber(row.spark),
        }));
    }, [rows]);

    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">
            <h2 className="text-xl font-semibold text-white">
                DuckDB vs Spark Benchmark Runtime
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-400">
                Runtime comparison across equivalent analytical workloads. Lower bars are
                faster. DuckDB is faster on compact local workloads, while Spark is built
                for distributed scale.
            </p>

            <div className="mt-6 h-[520px]">
                <ResponsiveContainer>
                    <BarChart data={chartRows}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="task" stroke="#94a3b8" minTickGap={20} />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                            formatter={(value) => [
                                `${asNumber(value).toFixed(3)} sec`,
                                "Runtime",
                            ]}
                        />
                        <Legend />
                        <Bar dataKey="DuckDB" name="DuckDB" fill="#38bdf8" />
                        <Bar dataKey="Spark" name="Spark" fill="#22c55e" />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}