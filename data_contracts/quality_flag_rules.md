# Quality Flag Rules (NOAA ISD)

This document defines how quality control (QC) flags are interpreted during cleaning.

---

## General Rule

- QC flags indicate reliability of a measurement
- Only values with acceptable QC flags will be used for modeling
- Invalid or low-quality values will be set to NULL or removed

---

## Wind (WND)

| Field | Rule |
|------|------|
| wind_direction_qc | Keep if QC indicates valid measurement |
| wind_speed_qc | Keep only high-quality observations |

Primary modeling dependency:
- wind_speed_ms must be reliable

---

## Temperature (TMP)

| Field | Rule |
|------|------|
| temperature_qc | Keep only valid atmospheric readings |

---

## Dew Point (DEW)

| Field | Rule |
|------|------|
| dew_point_qc | Keep only valid readings |

---

## Visibility (VIS)

| Field | Rule |
|------|------|
| visibility_qc | Keep only valid non-error values |

---

## Ceiling (CIG)

| Field | Rule |
|------|------|
| ceiling_qc | Keep only valid values |

---

## Pressure (SLP)

| Field | Rule |
|------|------|
| pressure_qc | Keep only valid values |

---

## v1 Simplification

For the first version of the project:

- strict QC filtering is preferred over complex imputation
- rows with invalid wind speed may be dropped
- QC flags will not be used as model features

---

## Notes

- exact QC code meanings depend on NOAA ISD documentation
- this document defines project-level policy, not raw code mapping
