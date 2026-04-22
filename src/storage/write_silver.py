def write_to_silver(df, target_path):
    """
    Layer 5 - Part B: Final Output Stage.
    Writes the processed, cleaned, and enriched weather data 
    into the Silver Layer in Parquet format.
    """
    print(f"--- [STORAGE] Writing finalized data to Silver Layer: {target_path} ---")
    
    df.write.mode("overwrite").parquet(target_path)
    
    print("--- [STORAGE] Silver write completed successfully. ---")
