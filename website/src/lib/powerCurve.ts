export type PowerCurveConfig = {
  cutInSpeedMs: number;
  ratedSpeedMs: number;
  cutOutSpeedMs: number;
};

export type PowerCurveResult = {
  windSpeedMs: number | null;
  capacityFactor: number | null;
  operatingRegion:
    | "missing"
    | "below_cut_in"
    | "ramp_up"
    | "rated"
    | "above_cut_out";
};

export const DEFAULT_POWER_CURVE_CONFIG: PowerCurveConfig = {
  cutInSpeedMs: 3,
  ratedSpeedMs: 12,
  cutOutSpeedMs: 25,
};

export function estimateCapacityFactor(
  windSpeedMs: number | null,
  config: PowerCurveConfig = DEFAULT_POWER_CURVE_CONFIG
): PowerCurveResult {
  if (windSpeedMs === null || !Number.isFinite(windSpeedMs)) {
    return {
      windSpeedMs: null,
      capacityFactor: null,
      operatingRegion: "missing",
    };
  }

  const { cutInSpeedMs, ratedSpeedMs, cutOutSpeedMs } = config;

  if (windSpeedMs < cutInSpeedMs) {
    return {
      windSpeedMs,
      capacityFactor: 0,
      operatingRegion: "below_cut_in",
    };
  }

  if (windSpeedMs >= cutOutSpeedMs) {
    return {
      windSpeedMs,
      capacityFactor: 0,
      operatingRegion: "above_cut_out",
    };
  }

  if (windSpeedMs >= ratedSpeedMs) {
    return {
      windSpeedMs,
      capacityFactor: 1,
      operatingRegion: "rated",
    };
  }

  const numerator = windSpeedMs ** 3 - cutInSpeedMs ** 3;
  const denominator = ratedSpeedMs ** 3 - cutInSpeedMs ** 3;
  const capacityFactor = Math.max(0, Math.min(1, numerator / denominator));

  return {
    windSpeedMs,
    capacityFactor,
    operatingRegion: "ramp_up",
  };
}

export function formatCapacityFactor(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return `${(value * 100).toFixed(1)}%`;
}