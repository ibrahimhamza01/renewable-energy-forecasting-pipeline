from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_split_column(
    df: DataFrame,
    date_col: str = "date",
    train_end: str = "2019-12-31",
    validation_end: str = "2022-12-31",
) -> DataFrame:
    """
    Assign train/validation/test splits using time only.

    Default split:
        train:      date <= 2019-12-31
        validation: 2020-01-01 through 2022-12-31
        test:       date >= 2023-01-01
    """

    date_expr = F.to_date(F.col(date_col))

    return (
        df.withColumn(date_col, date_expr)
        .withColumn(
            "split",
            F.when(F.col(date_col) <= F.lit(train_end), F.lit("train"))
            .when(F.col(date_col) <= F.lit(validation_end), F.lit("validation"))
            .otherwise(F.lit("test")),
        )
    )


def split_feature_table(
    df: DataFrame,
    split_col: str = "split",
) -> dict[str, DataFrame]:
    """
    Return separate DataFrames for train, validation, and test.
    """

    return {
        "train": df.filter(F.col(split_col) == "train"),
        "validation": df.filter(F.col(split_col) == "validation"),
        "test": df.filter(F.col(split_col) == "test"),
    }