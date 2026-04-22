# ETL Validation and Performance Review

## Execution Context
- **Tool:** Apache Spark (PySpark)
- **Environment:** AWS EC2 (t3.large/equivalent)
- **Scale:** 1.9 GB Raw Input -> 1.6 GB Processed Output

## Performance Metrics
- **Runtime:** ~75 minutes.
- **Resource Bottleneck:** Significant "Disk Spill" (5+ times) due to memory limits during the Global Sort phase.
- **Efficiency:** Despite resource constraints, Spark successfully managed the 1.6 GiB dataset without crashing, proving the robustness of the pipeline.

## Data Quality Checks (QA)
- **Schema Validation:** Verified. All columns (Wind, Temp, Pressure) match the expected Double/Decimal types.
- **Null Handling:** Quality Control (QC) flags were used to filter invalid measurements.
- **Spatial Integrity:** Station metadata (Lat/Lon) was successfully joined with hourly observations.

## Conclusion
The Silver Layer is **TRUSTED** and ready for the Layer 6 training pipeline.
