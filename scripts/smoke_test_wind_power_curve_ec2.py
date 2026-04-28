from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StructField, StructType

from src.physics.wind_power_curve import add_wind_power_columns

spark = (
    SparkSession.builder
    .appName("layer6_partA_ec2_smoke_test")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("wind_speed_ms", DoubleType(), True),
])

rows = [
    (0.0,),
    (3.5,),
    (6.0,),
    (13.0,),
    (20.0,),
    (30.0,),
    (None,),
    (-1.0,),
]

df = spark.createDataFrame(rows, schema=schema)

df = add_wind_power_columns(df)

df.show(truncate=False)

spark.stop()