from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

BUCKET = "alejandrog-alt-datsbd-s2026"

REGION_MONTHLY = f"s3a://{BUCKET}/gold/wind/region/monthly"
REGION_DAILY = f"s3a://{BUCKET}/gold/wind/region/daily"
STATION_DAILY = f"s3a://{BUCKET}/gold/wind/station/daily"
STATION_HOURLY = f"s3a://{BUCKET}/gold/wind/station/hourly"

OUTPUT = f"s3a://{BUCKET}/outputs/eda_gold_questions"


def main():
    spark = (
        SparkSession.builder
        .appName("Gold Wind EDA Questions")
        .getOrCreate()
    )

    print("\n==============================")
    print("Loading Gold tables")
    print("==============================")

    region_monthly = spark.read.parquet(REGION_MONTHLY)
    region_daily = spark.read.parquet(REGION_DAILY)
    station_daily = spark.read.parquet(STATION_DAILY)
    station_hourly = spark.read.parquet(STATION_HOURLY)

    print("region_monthly rows:", region_monthly.count())
    print("region_daily rows:", region_daily.count())
    print("station_daily rows:", station_daily.count())
    print("station_hourly rows:", station_hourly.count())

    # =========================================================
    # Q1. Where is wind potential strongest?
    # Use capacity_factor + wind_power_density by state/region
    # =========================================================
    print("\n\nQ1. WHERE IS WIND POTENTIAL STRONGEST?")

    q1_state = (
        region_monthly
        .groupBy("state", "region")
        .agg(
            F.round(F.avg("capacity_factor"), 4).alias("avg_capacity_factor"),
            F.round(F.avg("mean_wind_power_density_wm2"), 2).alias("avg_power_density_wm2"),
            F.round(F.avg("mean_wind_speed_ms"), 2).alias("avg_wind_speed_ms"),
            F.sum("total_observations").alias("total_observations")
        )
        .orderBy(F.desc("avg_capacity_factor"))
    )

    q1_state.show(20, truncate=False)
    q1_state.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q1_strongest_wind_by_state")

    # =========================================================
    # Q2. How does wind potential vary by season?
    # Monthly pattern by state/region
    # =========================================================
    print("\n\nQ2. HOW DOES WIND POTENTIAL VARY BY SEASON?")

    q2_monthly = (
        region_monthly
        .groupBy("state", "region", "month")
        .agg(
            F.round(F.avg("capacity_factor"), 4).alias("avg_capacity_factor"),
            F.round(F.avg("mean_wind_power_density_wm2"), 2).alias("avg_power_density_wm2"),
            F.round(F.avg("mean_wind_speed_ms"), 2).alias("avg_wind_speed_ms")
        )
        .orderBy("state", "month")
    )

    q2_monthly.show(100, truncate=False)
    q2_monthly.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q2_seasonal_wind_by_month")

    q2_best_months = (
        q2_monthly
        .withColumn(
            "rank",
            F.row_number().over(Window.partitionBy("state").orderBy(F.desc("avg_capacity_factor")))
        )
        .filter(F.col("rank") <= 3)
        .orderBy("state", "rank")
    )

    print("\nTop 3 wind months by state:")
    q2_best_months.show(50, truncate=False)
    q2_best_months.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q2_top_months_by_state")

    # =========================================================
    # Q3. Which regions have more stable wind patterns?
    # Lower stddev = more stable
    # =========================================================
    print("\n\nQ3. WHICH REGIONS HAVE MORE STABLE WIND PATTERNS?")

    q3_stability = (
        region_daily
        .groupBy("state", "region")
        .agg(
            F.round(F.avg("mean_wind_speed_ms"), 2).alias("avg_daily_wind_speed_ms"),
            F.round(F.stddev("mean_wind_speed_ms"), 2).alias("std_daily_wind_speed_ms"),
            F.round(F.avg("capacity_factor"), 4).alias("avg_capacity_factor"),
            F.round(F.stddev("capacity_factor"), 4).alias("std_capacity_factor"),
            F.count("*").alias("days")
        )
        .withColumn(
            "coefficient_of_variation",
            F.round(F.col("std_daily_wind_speed_ms") / F.col("avg_daily_wind_speed_ms"), 3)
        )
        .orderBy("coefficient_of_variation")
    )

    q3_stability.show(20, truncate=False)
    q3_stability.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q3_stability_by_state")

    # =========================================================
    # Q4. How much data is available after quality control?
    # Gold data availability summary
    # =========================================================
    print("\n\nQ4. HOW MUCH DATA REMAINS AFTER QUALITY CONTROL?")

    q4_daily_coverage = (
        station_daily
        .groupBy("year", "state")
        .agg(
            F.count("*").alias("station_day_rows"),
            F.countDistinct("station_id").alias("station_count"),
            F.sum("observation_count").alias("total_observations_after_qc"),
            F.round(F.avg("observation_count"), 2).alias("avg_observations_per_station_day")
        )
        .orderBy("year", "state")
    )

    q4_daily_coverage.show(100, truncate=False)
    q4_daily_coverage.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q4_qc_data_coverage")

    q4_summary = (
        station_daily
        .agg(
            F.count("*").alias("station_day_rows_after_qc"),
            F.countDistinct("station_id").alias("stations_after_qc"),
            F.sum("observation_count").alias("hourly_observations_after_qc"),
            F.round(F.avg("observation_count"), 2).alias("avg_obs_per_station_day")
        )
    )

    q4_summary.show(truncate=False)
    q4_summary.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q4_qc_summary")

    # =========================================================
    # Q5. What time scale is most useful?
    # Compare hourly, daily, monthly variability
    # =========================================================
    print("\n\nQ5. WHAT TIME SCALE IS MOST USEFUL?")

    hourly_summary = (
        station_hourly
        .agg(
            F.lit("hourly").alias("time_scale"),
            F.count("*").alias("rows"),
            F.round(F.avg("wind_speed_ms"), 2).alias("avg_wind_speed_ms"),
            F.round(F.stddev("wind_speed_ms"), 2).alias("std_wind_speed_ms"),
            F.round(F.avg("normalized_power"), 4).alias("avg_capacity_factor")
        )
    )

    daily_summary = (
        region_daily
        .agg(
            F.lit("daily").alias("time_scale"),
            F.count("*").alias("rows"),
            F.round(F.avg("mean_wind_speed_ms"), 2).alias("avg_wind_speed_ms"),
            F.round(F.stddev("mean_wind_speed_ms"), 2).alias("std_wind_speed_ms"),
            F.round(F.avg("capacity_factor"), 4).alias("avg_capacity_factor")
        )
    )

    monthly_summary = (
        region_monthly
        .agg(
            F.lit("monthly").alias("time_scale"),
            F.count("*").alias("rows"),
            F.round(F.avg("mean_wind_speed_ms"), 2).alias("avg_wind_speed_ms"),
            F.round(F.stddev("mean_wind_speed_ms"), 2).alias("std_wind_speed_ms"),
            F.round(F.avg("capacity_factor"), 4).alias("avg_capacity_factor")
        )
    )

    q5_timescale = hourly_summary.unionByName(daily_summary).unionByName(monthly_summary)

    q5_timescale.show(truncate=False)
    q5_timescale.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/q5_timescale_comparison")

    # =========================================================
    # FINAL INTERPRETATION TABLE
    # =========================================================
    print("\n\nFINAL EDA INTERPRETATION")
    print("""
Q1: Strongest wind potential = state/region with highest average capacity factor and wind power density.
Q2: Seasonal variation = months with higher capacity factor show stronger wind-energy potential.
Q3: Most stable regions = lowest coefficient of variation in daily wind speed.
Q4: QC result = station-day rows and hourly observations remaining after cleaning.
Q5: Best time scale:
    - Hourly: best for operational detail, but noisy.
    - Daily: best balance for forecasting and pattern detection.
    - Monthly: best for planning and seasonal summaries.
""")

    print(f"\nEDA outputs saved to: {OUTPUT}")
    spark.stop()


if __name__ == "__main__":
    main()