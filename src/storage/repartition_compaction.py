from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def compact_for_bronze(
    df: DataFrame,
    partition_col: str = "year",
    target_files_per_partition: int = 8,
) -> DataFrame:
    """
    Repartition bronze data to produce multiple files per partition value.

    Example:
    If partition_col='year' and target_files_per_partition=50,
    Spark will aim for roughly 50 files per year partition.

    This uses a temporary salt column so rows from the same year are spread
    across multiple Spark partitions before writing partitioned Parquet.
    """
    if target_files_per_partition < 1:
        raise ValueError("target_files_per_partition must be >= 1")

    salt_col = "__bronze_file_bucket"

    repartitioned_df = (
        df.withColumn(
            salt_col,
            F.pmod(F.xxhash64(F.monotonically_increasing_id()), F.lit(target_files_per_partition)),
        )
        .repartition(target_files_per_partition, partition_col, salt_col)
        .drop(salt_col)
    )

    return repartitioned_df