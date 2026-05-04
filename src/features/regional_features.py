"""
Layer 7/8 regional feature utilities for wind forecasting.

No paths are hardcoded here.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_state_long_run_features(df: DataFrame) -> DataFrame:
    """
    Add state-level historical summary features.

    These are descriptive regional features.
    For stricter production ML, these should be computed only on training years.
    """

    state_features = (
        df.groupBy("state")
        .agg(
            F.avg("daily_region_capacity_factor").alias("state_long_run_avg_cf"),
            F.stddev("daily_region_capacity_factor").alias("state_long_run_volatility"),
        )
    )

    return df.join(state_features, on="state", how="left")