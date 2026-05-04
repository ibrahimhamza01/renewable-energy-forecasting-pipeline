from src.common.paths import paths
from src.common.spark_utils import get_spark_session
from src.features.build_feature_table import build_training_table
from src.ml.dataset_split import split_feature_table


def main():
    spark = get_spark_session("build-training-tables")

    df = spark.read.parquet(paths.gold_wind_ml_base)

    training_df = build_training_table(
        df,
        date_col="date_utc",
        train_end="2019-12-31",
        validation_end="2022-12-31",
    )

    training_df.write.mode("overwrite").partitionBy("split").parquet(
        paths.gold_wind_ml_features
    )

    splits = split_feature_table(training_df)

    splits["train"].write.mode("overwrite").parquet(paths.gold_wind_ml_train)
    splits["validation"].write.mode("overwrite").parquet(paths.gold_wind_ml_validation)
    splits["test"].write.mode("overwrite").parquet(paths.gold_wind_ml_test)

    spark.stop()


if __name__ == "__main__":
    main()