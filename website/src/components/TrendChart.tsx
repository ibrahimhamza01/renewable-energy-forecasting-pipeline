"use client";

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
    Legend,
} from "recharts";

type TrendChartProps = {
    title: string;
    description: string;
    data: Record<string, string | number>[];
    xKey: string;
    yKeys: string[];
};

export default function TrendChart({
    title,
    description,
    data,
    xKey,
    yKeys,
}: TrendChartProps) {
    return (
        <section className="rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-lg">
            <div className="mb-4">
                <h2 className="text-xl font-semibold text-white">{title}</h2>
                <p className="mt-2 text-sm text-slate-400">{description}</p>
            </div>

            <div className="h-80 w-full">
                <ResponsiveContainer>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey={xKey}
                            label={{ value: xKey, position: "insideBottom", offset: -5 }}
                        />

                        <YAxis
                            label={{
                                value: "Capacity Factor",
                                angle: -90,
                                position: "insideLeft",
                            }}
                        />
                        <Tooltip />
                        <Legend />
                        {yKeys.map((key) => (
                            <Line
                                key={key}
                                type="monotone"
                                dataKey={key}
                                strokeWidth={2}
                                dot={false}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </section>
    );
}