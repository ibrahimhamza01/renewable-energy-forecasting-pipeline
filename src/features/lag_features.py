from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def add_lag_features(
    df: DataFrame,
    partition_cols: list[str] | None = None,
    order_col: str = "date",
    target_col: str = "capacity_factor",
    lag_days: list[int] | None = None,
) -> DataFrame:
    """
    Add lagged target features for wind forecasting.

    Expected grain:
        one row per region/date, usually state-date.

    Important:
        This function only uses past values, so it is safe from future leakage.
    """

    if partition_cols is None:
        partition_cols = ["state"]

    if lag_days is None:
        lag_days = [1, 2, 3, 7, 14, 30]

    window_spec = Window.partitionBy(*partition_cols).orderBy(F.col(order_col))

    out = df

    for lag in lag_days:
        out = out.withColumn(
            f"{target_col}_lag_{lag}d",
            F.lag(F.col(target_col), lag).over(window_spec),
        )

    return out


def add_lag_delta_features(
    df: DataFrame,
    target_col: str = "capacity_factor",
    base_lag: int = 1,
    comparison_lags: list[int] | None = None,
) -> DataFrame:
    """
    Add simple change features comparing recent wind potential to older lag values.
    """

    if comparison_lags is None:
        comparison_lags = [7, 14, 30]

    out = df

    base_col = f"{target_col}_lag_{base_lag}d"

    for lag in comparison_lags:
        lag_col = f"{target_col}_lag_{lag}d"
        out = out.withColumn(
            f"{target_col}_lag_{base_lag}d_minus_lag_{lag}d",
            F.col(base_col) - F.col(lag_col),
        )

    return out