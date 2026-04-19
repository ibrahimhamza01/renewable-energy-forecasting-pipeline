from src.common.spark_utils import get_remote_spark_session, stop_spark_session
from src.common.paths import paths

def main():
    spark = get_remote_spark_session("remote-smoke-test")

    print("Spark master:", spark.sparkContext.master)
    print("Spark version:", spark.version)

    # Tiny dataset
    df = spark.createDataFrame(
        [(1, "ok"), (2, "works")],
        ["id", "status"]
    )

    df.show()

    # Write to S3 (this is the REAL test)
    output_path = f"{paths.bronze_isd}/_smoke_test"

    print("Writing to:", output_path)

    df.write.mode("overwrite").parquet(output_path)

    print("Write complete")

    stop_spark_session(spark)


if __name__ == "__main__":
    main()