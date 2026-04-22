from pyspark.sql import SparkSession
from src.common.config import config

def main():
    spark = SparkSession.builder.getOrCreate()
    
    bronze_path = "s3a://bigdatafinal/bronze/isd"
    
    print(f"--- INSPECTION: Reading from Bronze Layer: {bronze_path} ---")
    
    try:
        df = spark.read.parquet(bronze_path)
        
        print("\n1. Şema (Columns):")
        df.printSchema()
        
        count = df.count()
        print(f"\n2. Toplam Satır Sayısı: {count}")
        
        if count > 0:
            print("\n3. İlk 5 Satır Örneği:")
            df.show(5, truncate=False)
        else:
            print(f"--- INSPECTION: No data found in Bronze Layer: {bronze_path} ---")
            
    except Exception as e:
        print(f"--- INSPECTION: Error occurred while reading from Bronze Layer: {bronze_path} ---")

if __name__ == "__main__":
    main()
