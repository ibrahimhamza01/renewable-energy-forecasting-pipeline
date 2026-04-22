from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder.getOrCreate()
    silver_path = "s3a://bigdatafinal/silver/weather" 
    
    print("\n" + "="*60)
    print(f"Silver layer: {silver_path}")
    print("="*60)
    
    try:
        df = spark.read.parquet(silver_path)
        
        check_cols = ['station_id', 'timestamp_utc', 'wind_speed_ms', 'temperature_c', 'LATITUDE', 'LONGITUDE']
        
        print(df.count())
        print("\n example rows:")
        df.select(*[c for c in check_cols if c in df.columns]).show(10, truncate=False)
        
        print("Ready")
        
    except Exception as e:
        print(f"Mistake on reading data")

if __name__ == "__main__":
    main()
