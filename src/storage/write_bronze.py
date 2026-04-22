def write_to_bronze(df, target_path):
    """Write sanitized bronze records to per-user prefix."""
    df.write.mode("overwrite").parquet(target_path)
