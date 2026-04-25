# Scaled ETL Validation

## Overview

This document summarizes validation results for the distributed ETL pipeline executed on NOAA ISD data.

- Years processed: 2018–2020  
- States: CA, TX, MN, FL  
- Execution environment: Spark on EC2, S3-backed storage  

---

## Data Volume

| Layer  | Rows |
|--------|------|
| Bronze | 35,504,907 |
| Silver | 28,893,512 |

- Rows removed during parsing/cleaning: 6,611,395  
- Retention rate: 81.38%

---

## Schema Validation

- All required fields are present in Silver:
  - station_id, timestamp_utc, date_utc
  - year, month, day, hour
  - state, region
  - wind_speed_ms, wind_direction_degrees
  - temperature_c, dew_point_c, sea_level_pressure_hpa
  - visibility_distance_m, ceiling_height_m

- Schema is consistent and stable across partitions.

---

## Partitioning Validation

Silver dataset is partitioned by:

- year  
- state  

### Partition distribution

| State | Rows |
|------|------|
| CA | 6,025,921 |
| FL | 4,736,837 |
| MN | 7,227,022 |
| TX | 10,903,732 |

- Data is reasonably balanced across partitions
- No major skew observed

---

## Data Quality

### Wind Speed

| Metric | Value |
|-------|------|
| Median | 3.1 m/s |
| p95 | 7.7 m/s |
| Max | 61.3 m/s |
| Zero wind rows | 5,948,808 (~20.6%) |

Interpretation:
- Distribution is physically realistic
- Zero wind values are expected in calm conditions

---

### Null Analysis

- No nulls in critical fields:
  - station_id
  - timestamp_utc
  - wind_speed_ms
  - state, year

- Nulls present in secondary fields:
  - pressure, visibility, ceiling, wind direction

These are expected due to missing observations in source data.

---

### Physical Validation

No invalid values detected:

- wind_speed_ms < 0 → 0 rows  
- wind_speed_ms > 75 → 0 rows  
- invalid wind directions → 0 rows  
- extreme temperature/pressure anomalies → 0 rows  

---

## Station Coverage

- Total stations: 626  
- States: 4  
- Years: 3  

| State | Stations |
|------|--------|
| CA | 169 |
| TX | 217 |
| MN | 100 |
| FL | 140 |

---

## Performance Validation

Query tested:

- Filter: year = 2020 AND state = TX  
- Rows returned: 3,568,158  
- Execution time: ~1.46 seconds  

Conclusion:

- Partition pruning is effective  
- Query latency is suitable for analytics  

---

## Conclusion

The Silver dataset:

- Successfully produced at scale on S3  
- Clean and physically valid  
- Properly partitioned  
- Efficient for analytical queries  

This dataset is approved as the **source of truth for downstream modeling and analytics**.