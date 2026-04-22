def compact_bronze_layer(df, num_files=10):
    """Mitigate small-file overhead."""
    return df.repartition(num_files)
