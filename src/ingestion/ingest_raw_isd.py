def ingest_raw_noaa(spark, source_path):
    """Parallel ingestion of multiple NOAA CSVs."""
    return spark.read.option("header", "true").csv(source_path)
