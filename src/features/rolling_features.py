from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def add_rolling_features(
    df: DataFrame,
    partition_cols: list[str] | None = None,
    order_col: str = "date",
    target_col: str = "capacity_factor",
    windows: list[int] | None = None,
) -> DataFrame:
    """
    Add rolling features using only prior days.

    The current row is excluded to avoid target leakage.
    """

    if partition_cols is None:
        partition_cols = ["state"]

    if windows is None:
        windows = [3, 7, 14, 30]

    out = df

    for window_days in windows:
        window_spec = (
            Window.partitionBy(*partition_cols)
            .orderBy(F.col(order_col))
            .rowsBetween(-window_days, -1)
        )

        out = (
            out.withColumn(
                f"{target_col}_rolling_{window_days}d_mean",
                F.avg(F.col(target_col)).over(window_spec),
            )
            .withColumn(
                f"{target_col}_rolling_{window_days}d_min",
                F.min(F.col(target_col)).over(window_spec),
            )
            .withColumn(
                f"{target_col}_rolling_{window_days}d_max",
                F.max(F.col(target_col)).over(window_spec),
            )
            .withColumn(
                f"{target_col}_rolling_{window_days}d_stddev",
                F.stddev(F.col(target_col)).over(window_spec),
            )
        )

    return out