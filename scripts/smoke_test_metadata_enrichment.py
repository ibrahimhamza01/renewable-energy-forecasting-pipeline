import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)
from pyspark.sql import functions as F

from src.cleaning.enrich_with_station_metadata import enrich_with_station_metadata


def main():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("smoke-test-metadata-enrichment")
        .getOrCreate()
    )

    weather_schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("timestamp_utc", TimestampType(), True),
        StructField("wind_direction_degrees", DoubleType(), True),
        StructField("wind_speed_ms", DoubleType(), True),
        StructField("temperature_c", DoubleType(), True),
        StructField("dew_point_c", DoubleType(), True),
        StructField("sea_level_pressure_hpa", DoubleType(), True),
        StructField("visibility_distance_m", DoubleType(), True),
        StructField("ceiling_height_m", DoubleType(), True),
    ])

    weather_data = [
        (
            "69002093218",   # should match sample metadata row
            None,
            180.0,
            5.144,
            21.5,
            18.0,
            1013.2,
            12000.0,
            800.0,
        ),
        (
            "00000000000",   # intentional non-match
            None,
            200.0,
            6.173,
            22.0,
            19.0,
            1012.0,
            9000.0,
            700.0,
        ),
    ]

    weather_df = spark.createDataFrame(weather_data, schema=weather_schema).withColumn(
        "timestamp_utc",
        F.to_timestamp(F.lit("2020-01-01T00:00:00"), "yyyy-MM-dd'T'HH:mm:ss"),
    )

    station_metadata_path = str(
        PROJECT_ROOT / "outputs" / "sample_runs" / "station_master_contiguous_us.csv"
    )

    station_df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(station_metadata_path)
    )

    enriched_df = enrich_with_station_metadata(
        weather_df=weather_df,
        station_df=station_df,
        station_col="station_id",
    )

    print("\n=== Enriched schema ===")
    enriched_df.printSchema()

    print("\n=== Enriched rows ===")
    enriched_df.show(truncate=False, vertical=True)

    print("\n=== Focused check ===")
    enriched_df.select(
        "station_id",
        "station_name",
        "state",
        "region",
        "latitude",
        "longitude",
        "elevation_m",
    ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()