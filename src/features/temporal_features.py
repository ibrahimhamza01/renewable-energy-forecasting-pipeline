"""
Layer 7/8 temporal feature utilities for wind forecasting.

No paths are hardcoded here.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_season_column(df: DataFrame, month_col: str = "month") -> DataFrame:
    return df.withColumn(
        "season",
        F.when(F.col(month_col).isin(12, 1, 2), F.lit("winter"))
        .when(F.col(month_col).isin(3, 4, 5), F.lit("spring"))
        .when(F.col(month_col).isin(6, 7, 8), F.lit("summer"))
        .when(F.col(month_col).isin(9, 10, 11), F.lit("fall"))
        .otherwise(F.lit(None)),
    )


def add_calendar_features(df: DataFrame, date_col: str = "date_utc") -> DataFrame:
    return (
        df.withColumn("day_of_year", F.dayofyear(F.col(date_col)))
        .withColumn("day_of_month", F.dayofmonth(F.col(date_col)))
        .withColumn("day_of_week", F.dayofweek(F.col(date_col)))
        .withColumn("is_weekend", F.col("day_of_week").isin(1, 7))
    )