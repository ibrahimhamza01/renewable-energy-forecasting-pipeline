# Wind Model Assumptions — Layer 6

## Turbine Model

We use a **generic normalized power curve** rather than a specific commercial
turbine model. This is appropriate because:

- The project goal is relative wind energy potential comparison across regions,
  not absolute energy production estimation.
- A normalized curve (0.0 to 1.0) allows capacity factor analysis without
  committing to a specific turbine rating.

### Power Curve Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Cut-in speed | 3.5 m/s | Typical utility-scale range (3-4 m/s) |
| Rated speed | 13.0 m/s | Typical utility-scale range (12-15 m/s) |
| Cut-out speed | 25.0 m/s | Industry standard |

### Cubic Region

Between cut-in and rated speed, power follows a cubic relationship:

```
P_normalized = ((v - v_cut_in) / (v_rated - v_cut_in))^3
```

This is a simplification. Real turbine curves are empirically measured and
show slight deviations from cubic behavior, but the cubic model is standard
for resource assessment.

## Air Density

We use standard sea-level air density (ρ = 1.225 kg/m³) for wind power
density calculations. In practice, air density varies with:

- Altitude (lower at higher elevations)
- Temperature (lower when warmer)
- Humidity (slightly lower when humid)

For our stations across CA, TX, MN, and FL, elevation ranges from near
sea level to ~650m. This introduces up to ~7% error in power density
estimates at higher-elevation stations, which is acceptable for a
comparative analysis.

## Observation Height

NOAA ISD wind measurements are typically taken at **10m anemometer height**,
not at typical turbine hub height (80-100m). Wind speed increases with
height following the power law:

```
v(h) = v(h_ref) * (h / h_ref)^alpha
```

where alpha ≈ 0.143 (1/7 power law) for open terrain.

We do **not** apply height correction in this analysis because:
- The project compares relative potential across regions
- All stations use similar measurement heights
- Height correction would uniformly scale all values

## Data Quality Filters

Before applying the power curve, we filter to:
- `is_wind_row_usable = true` (QC flags acceptable)
- `has_valid_wind_speed = true`
- `wind_speed_ms IS NOT NULL`
- `wind_speed_ms >= 0`
- `wind_speed_ms < 120 m/s` (physical sanity cap)

## Wind Direction Averaging

Daily mean wind direction is computed using circular averaging:
```
mean_direction = atan2(mean(sin(θ)), mean(cos(θ)))
```

This correctly handles the 360°/0° wraparound issue.

## NREL Wind Power Classes

Station locations are classified using approximate NREL wind power classes
based on mean wind speed at measurement height (10m):

| Class | Speed Range (m/s) | Rating |
|-------|-------------------|--------|
| 1 | < 4.4 | Poor |
| 2 | 4.4 – 5.1 | Marginal |
| 3 | 5.1 – 5.6 | Fair |
| 4 | 5.6 – 6.0 | Good |
| 5 | 6.0 – 6.4 | Excellent |
| 6 | 6.4 – 7.0 | Outstanding |
| 7 | ≥ 7.0 | Superb |
