from __future__ import annotations

from pathlib import Path

from src.common.spark_utils import get_local_spark_session, stop_spark_session
from src.parsing.parse_all_fields import add_all_parsed_weather_columns


OUTPUT_DIR = Path("outputs/sample_runs/parsed_sample")


def main() -> None:
    spark = get_local_spark_session("local-sample-pipeline")

    try:
        data = [
            (
                "324,1,H,0051,1",
                "+0093,1",
                "+0078,1",
                "10132,1",
                "016093,1,N,1",
                "02200,1,5,0",
            ),
            (
                "999,1,H,9999,1",
                "+9999,1",
                "-9999,1",
                "99999,1",
                "999999,1,9,1",
                "99999,1,9,9",
            ),
            (
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            (
                "bad,data",
                "bad,data",
                "bad,data",
                "bad,data",
                "bad,data",
                "bad,data",
            ),
        ]

        df = spark.createDataFrame(data, ["WND", "TMP", "DEW", "SLP", "VIS", "CIG"])
        parsed_df = add_all_parsed_weather_columns(df)

        output_path = str(OUTPUT_DIR.resolve())
        parsed_df.write.mode("overwrite").parquet(output_path)

        print(f"Parsed sample output written to: {output_path}")
        parsed_df.show(truncate=False, vertical=True)

    finally:
        stop_spark_session(spark)


if __name__ == "__main__":
    main()