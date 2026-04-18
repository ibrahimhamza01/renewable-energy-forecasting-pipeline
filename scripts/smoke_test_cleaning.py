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
)

from src.cleaning.clean_isd import clean_isd_dataframe


def main():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("smoke-test-cleaning")
        .getOrCreate()
    )

    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("timestamp_utc", StringType(), True),
        StructField("wind_direction_degrees", DoubleType(), True),
        StructField("wind_direction_qc", StringType(), True),
        StructField("wind_observation_type", StringType(), True),
        StructField("wind_speed_ms", DoubleType(), True),
        StructField("wind_speed_qc", StringType(), True),
        StructField("temperature_c", DoubleType(), True),
        StructField("temperature_qc", StringType(), True),
        StructField("dew_point_c", DoubleType(), True),
        StructField("dew_point_qc", StringType(), True),
        StructField("sea_level_pressure_hpa", DoubleType(), True),
        StructField("sea_level_pressure_qc", StringType(), True),
        StructField("visibility_distance_m", DoubleType(), True),
        StructField("visibility_distance_qc", StringType(), True),
        StructField("visibility_variability", StringType(), True),
        StructField("visibility_variability_qc", StringType(), True),
        StructField("ceiling_height_m", DoubleType(), True),
        StructField("ceiling_height_qc", StringType(), True),
        StructField("ceiling_determination_code", StringType(), True),
        StructField("ceiling_cavok", StringType(), True),
    ])

    data = [
        (
            "A",
            "2020-01-01T00:00:00",
            180.0,
            "1",
            "N",
            5.144,
            "1",
            21.5,
            "1",
            18.0,
            "1",
            1013.2,
            "1",
            12000.0,
            "1",
            "N",
            "1",
            800.0,
            "1",
            "A",
            "N",
        ),
        (
            "B",
            "2020-01-01T01:00:00",
            999.0,      # sentinel
            "1",
            "N",
            9999.0,     # sentinel
            "1",
            9999.0,     # sentinel
            "1",
            15.0,
            "1",
            1010.0,
            "1",
            10000.0,
            "1",
            "N",
            "1",
            500.0,
            "1",
            "A",
            "N",
        ),
        (
            "C",
            "2020-01-01T02:00:00",
            200.0,
            "1",
            "N",
            6.173,
            "3",        # bad QC
            22.0,
            "1",
            19.0,
            "1",
            1012.0,
            "1",
            9000.0,
            "1",
            "N",
            "1",
            700.0,
            "1",
            "A",
            "N",
        ),
    ]

    df = spark.createDataFrame(data, schema=schema)

    cleaned = clean_isd_dataframe(
        df,
        timestamp_col="timestamp_utc",
    )

    cleaned.printSchema()
    cleaned.show(truncate=False, vertical=True)

    spark.stop()


if __name__ == "__main__":
    main()