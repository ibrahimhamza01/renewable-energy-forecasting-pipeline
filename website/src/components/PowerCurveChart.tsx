import {
  DEFAULT_POWER_CURVE_CONFIG,
  estimateCapacityFactor,
  formatCapacityFactor,
} from "@/lib/powerCurve";

type PowerCurveChartProps = {
  windSpeedMs: number | null;
};

function buildCurvePoints() {
  const points = [];

  for (let speed = 0; speed <= 30; speed += 1) {
    const result = estimateCapacityFactor(speed);
    points.push({
      speed,
      capacityFactor: result.capacityFactor ?? 0,
    });
  }

  return points;
}

export default function PowerCurveChart({ windSpeedMs }: PowerCurveChartProps) {
  const curvePoints = buildCurvePoints();
  const current = estimateCapacityFactor(windSpeedMs);

  const chartWidth = 640;
  const chartHeight = 260;
  const padding = 36;

  const maxSpeed = 30;
  const maxCf = 1;

  function xScale(speed: number) {
    return padding + (speed / maxSpeed) * (chartWidth - padding * 2);
  }

  function yScale(cf: number) {
    return chartHeight - padding - (cf / maxCf) * (chartHeight - padding * 2);
  }

  const path = curvePoints
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${xScale(point.speed)} ${yScale(point.capacityFactor)}`;
    })
    .join(" ");

  const currentX =
    current.windSpeedMs === null ? null : xScale(Math.min(current.windSpeedMs, maxSpeed));
  const currentY =
    current.capacityFactor === null ? null : yScale(current.capacityFactor);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 shadow-lg">
      <div className="mb-4 flex flex-col gap-1">
        <h3 className="text-lg font-semibold text-white">Power Curve Operating Point</h3>
        <p className="text-sm text-slate-400">
          Cut-in {DEFAULT_POWER_CURVE_CONFIG.cutInSpeedMs} m/s · Rated{" "}
          {DEFAULT_POWER_CURVE_CONFIG.ratedSpeedMs} m/s · Cut-out{" "}
          {DEFAULT_POWER_CURVE_CONFIG.cutOutSpeedMs} m/s
        </p>
      </div>

      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="h-auto w-full">
        <line
          x1={padding}
          y1={chartHeight - padding}
          x2={chartWidth - padding}
          y2={chartHeight - padding}
          stroke="rgb(71 85 105)"
          strokeWidth="1"
        />
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={chartHeight - padding}
          stroke="rgb(71 85 105)"
          strokeWidth="1"
        />

        {[3, 12, 25].map((speed) => (
          <line
            key={speed}
            x1={xScale(speed)}
            y1={padding}
            x2={xScale(speed)}
            y2={chartHeight - padding}
            stroke="rgb(51 65 85)"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
        ))}

        <path d={path} fill="none" stroke="rgb(56 189 248)" strokeWidth="3" />

        {currentX !== null && currentY !== null && (
          <>
            <line
              x1={currentX}
              y1={currentY}
              x2={currentX}
              y2={chartHeight - padding}
              stroke="rgb(248 250 252)"
              strokeDasharray="4 4"
              strokeWidth="1"
            />
            <circle cx={currentX} cy={currentY} r="6" fill="rgb(34 197 94)" />
          </>
        )}

        <text x={padding} y={chartHeight - 8} fill="rgb(148 163 184)" fontSize="12">
          0 m/s
        </text>
        <text x={chartWidth - padding - 42} y={chartHeight - 8} fill="rgb(148 163 184)" fontSize="12">
          30 m/s
        </text>
        <text x={4} y={padding + 4} fill="rgb(148 163 184)" fontSize="12">
          100%
        </text>
      </svg>

      <div className="mt-4 rounded-xl bg-slate-900 p-4">
        <p className="text-sm text-slate-400">Current estimate</p>
        <p className="text-2xl font-bold text-white">
          {formatCapacityFactor(current.capacityFactor)}
        </p>
        <p className="text-sm text-slate-400">
          Operating region: <span className="text-slate-200">{current.operatingRegion}</span>
        </p>
      </div>
    </div>
  );
}