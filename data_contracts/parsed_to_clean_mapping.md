# Parsed → Clean Mapping

This document defines how parsed NOAA ISD weather fields are transformed into cleaned analysis-ready columns.

---

## Cleaning Goals

- convert sentinel values to NULL
- enforce basic quality control filtering
- standardize units
- normalize timestamps
- keep only fields needed for wind-focused analysis in v1

---

## Column Mapping

| Parsed Field | Clean Field | Cleaning Rule |
|-------------|------------|---------------|
| wind_direction_deg | wind_direction_deg | Keep if valid directional range |
| wind_direction_qc | wind_direction_qc | Preserve for audit/debugging |
| wind_type | wind_type | Preserve as parsed |
| wind_speed_ms | wind_speed_ms | Keep only plausible non-negative values |
| wind_speed_qc | wind_speed_qc | Use in quality filtering |
| temperature_c | temperature_c | Keep only plausible atmospheric values |
| temperature_qc | temperature_qc | Use in quality filtering |
| dew_point_c | dew_point_c | Keep only plausible atmospheric values |
| dew_point_qc | dew_point_qc | Use in quality filtering |
| visibility_m | visibility_m | Keep only non-negative values |
| visibility_qc | visibility_qc | Preserve for filtering/audit |
| ceiling_height_m | ceiling_height_m | Keep only non-negative values |
| ceiling_qc | ceiling_qc | Preserve for filtering/audit |
| sea_level_pressure_hpa | sea_level_pressure_hpa | Keep only plausible pressure values |
| pressure_qc | pressure_qc | Preserve for filtering/audit |

---

## Standardization Rules

- wind speed stored in meters per second
- temperature stored in degrees Celsius
- dew point stored in degrees Celsius
- visibility stored in meters
- ceiling height stored in meters
- sea level pressure stored in hPa
- timestamps normalized to UTC

---

## Null / Sentinel Handling

- sentinel and missing encoded values become NULL
- invalid parsed numeric values become NULL
- rows with unusable wind speed may be dropped in downstream wind modeling datasets

---

## v1 Clean Dataset Scope

The cleaned v1 dataset will prioritize:

- station metadata
- timestamp
- wind measurements
- core supporting weather variables

The cleaned v1 dataset will exclude:

- sparse optional NOAA ISD auxiliary fields
- non-core derived features
- solar-related logic

---

## Notes

- exact QC acceptance/rejection rules are defined separately in `quality_flag_rules.md`
- this document defines cleaned column expectations, not parser implementation
