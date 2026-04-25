from pyspark.sql import DataFrame


def compact_for_bronze(
    df: DataFrame,
    partition_col: str = "year",
    target_files_per_partition: int = 8,
) -> DataFrame:
    """
    Repartition bronze data to reduce small-file output.

    Example:
    If partition_col='year' and target_files_per_partition=8,
    Spark will aim for roughly 8 files per year partition.
    """
    return df.repartition(target_files_per_partition, partition_col)