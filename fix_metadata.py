from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

path = "outputs/sample_runs/station_master_contiguous_us.csv"
df = spark.read.option("header", "true").csv(path)


df_fixed = df.withColumn(
    "station_id", 
    F.concat(F.col("USAF"), F.format_string("%05d", F.col("WBAN").cast("int")))
)

df_fixed.write.mode("overwrite").option("header", "true").csv("outputs/sample_runs/fixed_metadata")

import os
import glob
csv_file = glob.glob("outputs/sample_runs/fixed_metadata/*.csv")[0]
os.replace(csv_file, path)
