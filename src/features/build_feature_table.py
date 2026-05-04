from pyspark.sql import DataFrame

from src.features.lag_features import add_lag_features, add_lag_delta_features
from src.features.rolling_features import add_rolling_features
from src.features.temporal_features import add_temporal_features

from src.ml.dataset_split import add_split_column


def build_feature_table(
    df: DataFrame,
    date_col: str = "date_utc",
    target_col: str = "daily_region_capacity_factor",
    partition_cols: list[str] | None = None,
) -> DataFrame:
    if partition_cols is None:
        partition_cols = ["state"]

    df = add_temporal_features(df, date_col=date_col)

    df = add_lag_features(
        df,
        partition_cols=partition_cols,
        order_col=date_col,
        target_col=target_col,
    )

    df = add_lag_delta_features(
        df,
        target_col=target_col,
    )

    df = add_rolling_features(
        df,
        partition_cols=partition_cols,
        order_col=date_col,
        target_col=target_col,
    )

    return df

def build_training_table(
    df: DataFrame,
    date_col: str = "date_utc",
    target_col: str = "daily_region_capacity_factor",
    partition_cols: list[str] | None = None,
    train_end: str = "2019-12-31",
    validation_end: str = "2022-12-31",
) -> DataFrame:
    feature_df = build_feature_table(
        df,
        date_col=date_col,
        target_col=target_col,
        partition_cols=partition_cols,
    )

    return add_split_column(
        feature_df,
        date_col=date_col,
        train_end=train_end,
        validation_end=validation_end,
    )