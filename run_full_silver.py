from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.common.config import config
from src.parsing.parse_all_fields import add_all_parsed_weather_columns
from src.cleaning.clean_isd import clean_isd_dataframe
from src.cleaning.enrich_with_station_metadata import enrich_with_station_metadata

def main():
    spark = SparkSession.builder.getOrCreate()
    
    bronze_path = "s3a://bigdatafinal/bronze/isd"
    silver_path = "s3a://bigdatafinal/silver/weather"
    metadata_path = "outputs/sample_runs/station_master_contiguous_us.csv"
    
    
    df_bronze = spark.read.parquet(bronze_path)
    
   
    print("Step 0: Column names standardizing...")
    df_standardized = df_bronze \
        .withColumnRenamed("STATION", "station_id") \
        .withColumnRenamed("DATE", "timestamp_utc")
    
    
    print("Step 1: Parsing")
    df_parsed = add_all_parsed_weather_columns(df_standardized)
    
    print("Step 2: Cleaning")
    df_cleaned = clean_isd_dataframe(df_parsed)
    
    print(f"Step 3: Station metada")
    station_df = spark.read.option("header", "true").csv(metadata_path)
    
    print("Step 4: Enrichment...")
    df_enriched = enrich_with_station_metadata(df_cleaned, station_df)
    
    print(f"Step 5: Silver layer writing: {silver_path}")
    df_enriched.write.mode("overwrite").parquet(silver_path)
    
  

if __name__ == "__main__":
    main()
