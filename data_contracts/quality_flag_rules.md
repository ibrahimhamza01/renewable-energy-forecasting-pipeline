# Quality Flag Rules (NOAA ISD)

This document defines how quality control (QC) flags and raw values are interpreted
during cleaning for the wind energy forecasting pipeline.

This is a **data contract**: it reflects exactly how `clean_isd.py` behaves.

---

## General Principles

- QC flags indicate reliability of a measurement
- Only values with acceptable QC flags are retained
- Invalid, low-quality, or suspect values are set to **NULL**
- No imputation is performed at this stage
- Cleaning is **field-level**, not row-level (except for wind usability)

---

## Sentinel Handling

Before QC filtering:

- Known sentinel values are converted to NULL

Examples:
- `9999`, `999.9` → missing wind speed / temperature
- `99999`, `999999` → missing pressure / visibility / ceiling

This is applied consistently across all fields.

---

## Range Validation

After sentinel handling and QC filtering:

Values outside physically plausible bounds are set to NULL.

Examples:

| Field | Valid Range |
|------|------------|
| wind_direction_degrees | 0–360 |
| wind_speed | 0–150 m/s |
| temperature | -90°C to 60°C |
| dew_point | -100°C to 50°C |
| pressure | 800–1100 hPa |
| visibility | 0–200,000 m |
| ceiling_height | 0–30,000 m |

---

## QC Filtering Rules

QC filtering is applied per field using `apply_qc_filter`.

### General Behavior

- If QC flag is **not in allowed set → value = NULL**
- If QC flag is **missing → value = NULL (default behavior)**

---

## Wind (Critical Field)

| Field | Rule |
|------|------|
| wind_speed_qc | Only allowed QC values are retained |
| wind_direction_qc | Only allowed QC values are retained |

### Critical Rule

Wind speed is the **primary modeling signal**.

A row is considered usable for wind modeling only if:

- `wind_speed_ms IS NOT NULL`
- `timestamp_utc IS NOT NULL`

This is enforced via:

- `enforce_required_wind_fields`
- `is_wind_row_usable = TRUE`

---

## Temperature (TMP)

| Field | Rule |
|------|------|
| temperature_qc | Must be valid or set to NULL |

Used for:
- sanity checks
- derived consistency features

---

## Dew Point (DEW)

| Field | Rule |
|------|------|
| dew_point_qc | Must be valid or set to NULL |

Also used in:
- temperature/dew consistency checks

---

## Pressure (SLP)

| Field | Rule |
|------|------|
| sea_level_pressure_qc | Must be valid or set to NULL |

---

## Visibility (VIS)

| Field | Rule |
|------|------|
| visibility_distance_qc | Must be valid or set to NULL |

---

## Ceiling (CIG)

| Field | Rule |
|------|------|
| ceiling_height_qc | Must be valid or set to NULL |

---

## Consistency Checks

After cleaning and unit conversion:

- Temperature ≥ Dew Point (physically consistent)
- Flagged as:
  - `temp_dew_consistent = TRUE/FALSE`

---

## Derived Audit Flags

The following flags are added:

- `has_valid_wind_speed`
- `has_valid_timestamp`
- `is_core_row_complete`
- `is_wind_row_usable`

These are used for:
- filtering
- diagnostics
- downstream validation

---

## Modeling Readiness Definition

A row is considered **valid for wind modeling** if:

- `is_wind_row_usable = TRUE`

This implies:

- wind speed is valid and usable
- timestamp is valid
- QC + bounds + sentinel rules have been applied

---

## v1 Design Decisions

- Prefer strict filtering over imputation
- Do not use QC flags as model features
- Preserve non-wind fields even if partially missing
- Prioritize reliability of wind speed over completeness of all variables

---

## Notes

- QC code meanings come from NOAA ISD documentation
- This document defines **project-level behavior**, not raw encoding
- Any change to cleaning logic must be reflected here