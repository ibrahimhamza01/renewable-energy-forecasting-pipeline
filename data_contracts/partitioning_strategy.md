# Partitioning Strategy — Silver Weather Data

## Overview

This document defines the physical layout and access patterns for the Silver weather dataset.

---

## Storage Location

- Format: Parquet  
- Storage: S3  
- Path structure:

```

silver/weather/year=<year>/state=<state>/

````

---

## Partitioning Scheme

The Silver dataset is partitioned by:

- `year`
- `state`

### Rationale

- Enables efficient time-based filtering (common in forecasting)
- Enables regional/state-level analysis
- Supports partition pruning in Spark queries

---

## Expected Partition Characteristics

- Each partition contains millions of rows
- File sizes are optimized via repartitioning during write
- Avoids small file problem

---

## Access Requirements

All downstream consumers **must**:

- Filter by `year` whenever possible
- Filter by `state` when doing regional analysis

Example:

```python
df.filter((F.col("year") == 2020) & (F.col("state") == "TX"))
````

---

## Guarantees

The Silver dataset guarantees:

* Valid timestamps (`timestamp_utc`)
* Clean wind speed (`wind_speed_ms`)
* Valid geographic mapping (`state`, `region`)
* Physically plausible weather values

---

## Non-Guaranteed Fields

Some fields may contain nulls due to source limitations:

* wind_direction_degrees
* visibility_distance_m
* ceiling_height_m
* sea_level_pressure_hpa

Downstream systems must handle these appropriately.

---

## Future Scaling

* Partitioning scheme will remain stable for full dataset (1995–2025)
* Additional partitioning (e.g., month) may be introduced only if required for performance

---

## Contract Summary

* Partition keys: `year`, `state`
* Storage format: Parquet
* Source of truth: Silver layer
* Downstream reads: must be partition-aware