from pyspark.sql import SparkSession

from src.features.lag_features import add_lag_features, add_lag_delta_features


def test_add_lag_features_no_future_leakage():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-lag-features")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-01", 0.10),
        ("TX", "2020-01-02", 0.20),
        ("TX", "2020-01-03", 0.30),
        ("TX", "2020-01-04", 0.40),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        add_lag_features(
            df,
            partition_cols=["state"],
            order_col="date",
            target_col="capacity_factor",
            lag_days=[1, 2],
        )
        .orderBy("date")
        .collect()
    )

    assert result[0]["capacity_factor_lag_1d"] is None
    assert result[0]["capacity_factor_lag_2d"] is None

    assert result[1]["capacity_factor_lag_1d"] == 0.10
    assert result[1]["capacity_factor_lag_2d"] is None

    assert result[2]["capacity_factor_lag_1d"] == 0.20
    assert result[2]["capacity_factor_lag_2d"] == 0.10

    assert result[3]["capacity_factor_lag_1d"] == 0.30
    assert result[3]["capacity_factor_lag_2d"] == 0.20


def test_add_lag_features_partitioned_by_state():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-lag-partitions")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-01", 0.10),
        ("TX", "2020-01-02", 0.20),
        ("CA", "2020-01-01", 0.50),
        ("CA", "2020-01-02", 0.60),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        add_lag_features(
            df,
            partition_cols=["state"],
            order_col="date",
            target_col="capacity_factor",
            lag_days=[1],
        )
        .orderBy("state", "date")
        .collect()
    )

    ca_day_1 = result[0]
    ca_day_2 = result[1]
    tx_day_1 = result[2]
    tx_day_2 = result[3]

    assert ca_day_1["capacity_factor_lag_1d"] is None
    assert ca_day_2["capacity_factor_lag_1d"] == 0.50

    assert tx_day_1["capacity_factor_lag_1d"] is None
    assert tx_day_2["capacity_factor_lag_1d"] == 0.10


def test_add_lag_delta_features():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-lag-deltas")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-10", 0.30, 0.10),
    ]

    df = spark.createDataFrame(
        data,
        [
            "state",
            "date",
            "capacity_factor_lag_1d",
            "capacity_factor_lag_7d",
        ],
    )

    result = add_lag_delta_features(
        df,
        target_col="capacity_factor",
        base_lag=1,
        comparison_lags=[7],
    ).collect()[0]

    assert round(result["capacity_factor_lag_1d_minus_lag_7d"], 6) == 0.20

from src.features.rolling_features import add_rolling_features


def test_rolling_features_no_leakage():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-rolling-features")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-01", 1.0),
        ("TX", "2020-01-02", 2.0),
        ("TX", "2020-01-03", 3.0),
        ("TX", "2020-01-04", 4.0),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        add_rolling_features(
            df,
            partition_cols=["state"],
            order_col="date",
            target_col="capacity_factor",
            windows=[2],
        )
        .orderBy("date")
        .collect()
    )

    # Day 1 → no history
    assert result[0]["capacity_factor_rolling_2d_mean"] is None

    # Day 2 → only day 1
    assert result[1]["capacity_factor_rolling_2d_mean"] == 1.0

    # Day 3 → days 1 & 2 → mean = 1.5
    assert result[2]["capacity_factor_rolling_2d_mean"] == 1.5

    # Day 4 → days 2 & 3 → mean = 2.5
    assert result[3]["capacity_factor_rolling_2d_mean"] == 2.5


def test_rolling_features_partition_isolation():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-rolling-partitions")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-01", 1.0),
        ("TX", "2020-01-02", 2.0),
        ("CA", "2020-01-01", 10.0),
        ("CA", "2020-01-02", 20.0),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        add_rolling_features(
            df,
            partition_cols=["state"],
            order_col="date",
            target_col="capacity_factor",
            windows=[1],
        )
        .orderBy("state", "date")
        .collect()
    )

    # CA partition
    assert result[0]["capacity_factor_rolling_1d_mean"] is None
    assert result[1]["capacity_factor_rolling_1d_mean"] == 10.0

    # TX partition
    assert result[2]["capacity_factor_rolling_1d_mean"] is None
    assert result[3]["capacity_factor_rolling_1d_mean"] == 1.0

from src.features.temporal_features import add_temporal_features


def test_add_temporal_features():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-temporal-features")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-04", 0.10),
        ("TX", "2020-07-15", 0.20),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date_utc", "capacity_factor"],
    )

    result = (
        add_temporal_features(df, date_col="date_utc")
        .orderBy("date_utc")
        .collect()
    )

    assert result[0]["year"] == 2020
    assert result[0]["month"] == 1
    assert result[0]["day_of_year"] == 4
    assert result[0]["is_weekend"] is True
    assert result[0]["season"] == "winter"

    assert result[1]["month"] == 7
    assert result[1]["season"] == "summer"

from src.features.build_feature_table import build_feature_table


def test_build_feature_table_runs():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-build-feature-table")
        .getOrCreate()
    )

    data = [
        ("TX", "2020-01-01", 0.10),
        ("TX", "2020-01-02", 0.20),
        ("TX", "2020-01-03", 0.30),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = build_feature_table(
        df,
        date_col="date",
        target_col="capacity_factor",
        partition_cols=["state"],
    )

    cols = result.columns

    assert "capacity_factor_lag_1d" in cols
    assert "capacity_factor_rolling_3d_mean" in cols
    assert "month" in cols

from src.ml.dataset_split import add_split_column, split_feature_table


def test_add_split_column_time_based():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-dataset-split")
        .getOrCreate()
    )

    data = [
        ("TX", "2019-12-31", 0.10),
        ("TX", "2020-01-01", 0.20),
        ("TX", "2023-01-01", 0.30),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        add_split_column(
            df,
            date_col="date",
            train_end="2019-12-31",
            validation_end="2022-12-31",
        )
        .orderBy("date")
        .collect()
    )

    assert result[0]["split"] == "train"
    assert result[1]["split"] == "validation"
    assert result[2]["split"] == "test"


def test_split_feature_table_returns_three_splits():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-split-feature-table")
        .getOrCreate()
    )

    data = [
        ("TX", "train"),
        ("CA", "validation"),
        ("MN", "test"),
    ]

    df = spark.createDataFrame(data, ["state", "split"])

    splits = split_feature_table(df)

    assert splits["train"].count() == 1
    assert splits["validation"].count() == 1
    assert splits["test"].count() == 1

from src.features.build_feature_table import build_training_table


def test_build_training_table_adds_split():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-build-training-table")
        .getOrCreate()
    )

    data = [
        ("TX", "2019-12-31", 0.10),
        ("TX", "2020-01-01", 0.20),
        ("TX", "2023-01-01", 0.30),
    ]

    df = spark.createDataFrame(
        data,
        ["state", "date", "capacity_factor"],
    )

    result = (
        build_training_table(
            df,
            date_col="date",
            target_col="capacity_factor",
            partition_cols=["state"],
            train_end="2019-12-31",
            validation_end="2022-12-31",
        )
        .orderBy("date")
        .collect()
    )

    assert result[0]["split"] == "train"
    assert result[1]["split"] == "validation"
    assert result[2]["split"] == "test"