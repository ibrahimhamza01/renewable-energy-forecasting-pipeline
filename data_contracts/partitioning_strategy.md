# Partitioning and Storage Strategy - Silver Layer

## Strategy Overview
The Silver weather data is stored in **Parquet** format with a specific focus on query performance for wind energy analytics.

## Physical Layout
- **Source:** s3a://bigdatafinal/bronze/isd
- **Target:** s3a://bigdatafinal/silver/weather
- **Format:** Parquet (Snappy compressed)
- **File Count:** 8 optimized files (~200 MiB each)

## Design Decisions
1. **Compaction:** We consolidated thousands of small NOAA CSV files into 8 large Parquet files to mitigate the "small-file overhead" in S3/Spark.
2. **Sorting:** Data is sorted by `station_id` and `timestamp_utc`. This ensures that downstream time-series analysis for specific stations is extremely fast.
3. **Schema Stability:** All meteorological units are standardized (e.g., Wind Speed in m/s, Temperature in Celsius).

## Downstream Impact
Data Scientists should only read the **Silver** layer. The Bronze layer is considered "raw" and should not be used for modeling.
