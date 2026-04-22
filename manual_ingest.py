from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.bucket.noaa-global-hourly-pds.aws.credentials.provider", "org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider") \
    .getOrCreate()

file_name = "01001099999.csv"
source_path = f"s3a://noaa-global-hourly-pds/2024/{file_name}"
target_path = "s3a://bigdatafinal/bronze/isd"


try:
    
    df = spark.read.option("header", "true").csv(source_path)
    
    df.write.mode("overwrite").parquet(target_path)
    
except Exception as e:
    print('Mistake happened during manual ingest:')
