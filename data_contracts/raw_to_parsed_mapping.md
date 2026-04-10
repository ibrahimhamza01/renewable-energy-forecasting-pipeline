# Raw → Parsed Mapping (NOAA ISD)

This document defines how raw NOAA ISD fields are transformed into parsed structured columns.

---

## Core Fields (Raw)

| Field | Description |
|------|-------------|
| STATION | Station identifier |
| DATE | Timestamp |
| SOURCE | Data source |
| LATITUDE | Station latitude |
| LONGITUDE | Station longitude |
| ELEVATION | Station elevation |
| NAME | Station name |
| REPORT_TYPE | Report type |
| QUALITY_CONTROL | QC flag |
| WND | Encoded wind data |
| CIG | Encoded ceiling data |
| VIS | Encoded visibility data |
| TMP | Encoded temperature |
| DEW | Encoded dew point |
| SLP | Encoded sea level pressure |

---

## Parsed Outputs

### Wind (WND)

Raw format example:
```
WND = "045,1,N,0100,1"
```

Parsed fields:

| Parsed Field | Description |
|-------------|------------|
| wind_direction_deg | Wind direction (degrees) |
| wind_direction_qc | QC flag |
| wind_type | Wind type |
| wind_speed_ms | Wind speed (m/s) |
| wind_speed_qc | QC flag |

---

### Temperature (TMP)

| Parsed Field | Description |
|-------------|------------|
| temperature_c | Air temperature |
| temperature_qc | QC flag |

---

### Dew Point (DEW)

| Parsed Field | Description |
|-------------|------------|
| dew_point_c | Dew point |
| dew_point_qc | QC flag |

---

### Visibility (VIS)

| Parsed Field | Description |
|-------------|------------|
| visibility_m | Visibility |
| visibility_qc | QC flag |

---

### Ceiling (CIG)

| Parsed Field | Description |
|-------------|------------|
| ceiling_height_m | Ceiling height |
| ceiling_qc | QC flag |

---

### Pressure (SLP)

| Parsed Field | Description |
|-------------|------------|
| sea_level_pressure_hpa | Pressure |
| pressure_qc | QC flag |

---

## Notes

- Sentinel values will be converted to NULL
- QC flags will be used in cleaning stage
- Only core weather fields are included in v1
- Sparse optional fields are excluded for now

---

## Scope Decision

- Wind is the primary modeling target
- Other weather variables are supporting features
- Solar-related fields are out of scope
