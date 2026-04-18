# src/cleaning/run_local_sample_pipeline.py

from __future__ import annotations

from pyspark.sql import functions as F

from src.cleaning.clean_isd import build_cleaned_weather_table
from src.cleaning.enrich_with_station_metadata import enrich_with_station_metadata
from src.common.io_utils import read_parquet, write_parquet
from src.common.paths import paths
from src.common.spark_utils import get_local_spark_session


def load_station_metadata(spark, csv_path: str):
    return (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(csv_path)
    )


def main() -> None:
    spark = get_local_spark_session(app_name="local-sample-cleaned-pipeline")

    print(f"\nReading parsed sample from: {paths.parsed_sample}")
    parsed_df = read_parquet(spark, paths.parsed_sample)

    print("\nParsed sample schema:")
    parsed_df.printSchema()

    # Ensure timestamp_utc is a proper timestamp only if it is currently a string.
    if "timestamp_utc" in parsed_df.columns:
        timestamp_dtype = dict(parsed_df.dtypes).get("timestamp_utc")

        if timestamp_dtype == "string":
            parsed_df = parsed_df.withColumn(
                "timestamp_utc",
                F.coalesce(
                    F.to_timestamp(
                        F.regexp_replace(F.col("timestamp_utc"), r"Z$", ""),
                        "yyyy-MM-dd'T'HH:mm:ss",
                    ),
                    F.to_timestamp(F.col("timestamp_utc"), "yyyy-MM-dd HH:mm:ss"),
                ),
            )

    print("\nCleaning parsed weather data...")
    cleaned_df = build_cleaned_weather_table(
        parsed_df,
        timestamp_col="timestamp_utc",
        require_wind_speed=True,
        require_timestamp=True,
        add_audit_columns=True,
        keep_extra_columns=True,
    )

    print("\nCleaned schema:")
    cleaned_df.printSchema()

    print(f"\nReading station metadata from: {paths.station_master_contiguous_us}")
    station_df = load_station_metadata(spark, paths.station_master_contiguous_us)

    print("\nStation metadata schema:")
    station_df.printSchema()

    print("\nEnriching with station metadata...")
    enriched_df = enrich_with_station_metadata(
        weather_df=cleaned_df,
        station_df=station_df,
        station_col="station_id",
    )

    print("\nEnriched schema:")
    enriched_df.printSchema()

    print("\nSample enriched rows:")
    enriched_df.show(10, truncate=False, vertical=True)

    print(f"\nWriting cleaned enriched parquet to: {paths.cleaned_enriched_sample}")
    write_parquet(
        enriched_df,
        output_path=paths.cleaned_enriched_sample,
        mode="overwrite",
    )

    print("\nLocal cleaned enriched pipeline completed successfully.")

    spark.stop()


if __name__ == "__main__":
    main()