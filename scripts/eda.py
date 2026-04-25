from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, save PNG to disk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


# =============================================================================
# CONFIG
# =============================================================================
YEAR = 2020

# 5 stations per state — major airports with reliable data
# Format: (state, station_id, friendly_name)
STATIONS = [
    # California
    ("CA", "72295023174", "Los Angeles INTL"),
    ("CA", "72494023234", "San Francisco INTL"),
    ("CA", "72290023188", "San Diego INTL"),
    ("CA", "72389693206", "Long Beach"),
    ("CA", "72493023240", "Hayward Air Term"),
    # Texas
    ("TX", "72243012960", "Houston Hobby"),
    ("TX", "72259003927", "Dallas-Fort Worth INTL"),
    ("TX", "72253012921", "San Antonio INTL"),
    ("TX", "72250012919", "Brownsville"),
    ("TX", "72265023044", "Midland INTL"),
    # Minnesota
    ("MN", "72658014922", "Minneapolis-St Paul INTL"),
    ("MN", "72756594931", "International Falls"),
    ("MN", "72655094960", "Duluth"),
    ("MN", "72657014926", "St Cloud Regional"),
    ("MN", "72644094983", "Brainerd"),
    # Florida
    ("FL", "72202012839", "Miami INTL"),
    ("FL", "72205012815", "Orlando INTL"),
    ("FL", "72211012842", "Tampa INTL"),
    ("FL", "72206013889", "Jacksonville INTL"),
    ("FL", "72204012844", "Fort Lauderdale"),
]

OUTPUT_DIR = Path("outputs/figures")
METRICS_DIR = Path("outputs/metrics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

STATE_COLORS = {
    "CA": "#1f77b4",
    "TX": "#d62728",
    "MN": "#2ca02c",
    "FL": "#ff7f0e",
}


# =============================================================================
# WND PARSER (inlined from src/parsing/parse_wnd.py)
# =============================================================================
WND_PART_COUNT = 5
DIRECTION_SENTINEL = "999"
SPEED_SENTINEL = "9999"


def add_parsed_wnd_columns(df: DataFrame, source_col: str = "WND") -> DataFrame:
    """
    Parse NOAA ISD WND field into separate columns.

    Raw format: "direction,direction_qc,type_code,speed,speed_qc"
    Example:    "324,1,H,0051,1"
        - direction:  degrees (999 = missing)
        - speed:      tenths of m/s (9999 = missing)
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not found")

    parts = F.split(F.col(source_col), ",")

    direction_raw = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(0)))
    direction_qc = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(1)))
    type_code = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(2)))
    speed_raw = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(3)))
    speed_qc = F.when(F.size(parts) == WND_PART_COUNT, F.trim(parts.getItem(4)))

    direction_int = direction_raw.cast("int")
    speed_int = speed_raw.cast("int")

    wind_direction_degrees = (
        F.when(
            direction_raw.isNull()
            | (direction_raw == "")
            | (direction_raw == DIRECTION_SENTINEL),
            F.lit(None),
        )
        .when(direction_int.isNull(), F.lit(None))
        .when((direction_int < 0) | (direction_int > 360), F.lit(None))
        .otherwise(direction_int)
    )

    wind_speed_ms = (
        F.when(
            speed_raw.isNull()
            | (speed_raw == "")
            | (speed_raw == SPEED_SENTINEL),
            F.lit(None),
        )
        .when(speed_int.isNull(), F.lit(None))
        .when(speed_int < 0, F.lit(None))
        .otherwise(speed_int / F.lit(10.0))
    )

    return (
        df.withColumn("wind_direction_degrees", wind_direction_degrees)
        .withColumn("wind_direction_qc", direction_qc)
        .withColumn("wind_observation_type", type_code)
        .withColumn("wind_speed_ms", wind_speed_ms)
        .withColumn("wind_speed_qc", speed_qc)
    )


# =============================================================================
# UTILITIES
# =============================================================================
def save_fig(fig, name: str) -> None:
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {path}")


def validate_stations(spark: SparkSession, year: int, stations: list) -> list:
    """Filter STATIONS list to only those whose CSV exists in the NOAA bucket."""
    hadoop_conf = spark._jsc.hadoopConfiguration()
    FileSystem = spark._jvm.org.apache.hadoop.fs.FileSystem
    Path_ = spark._jvm.org.apache.hadoop.fs.Path
    URI = spark._jvm.java.net.URI
    fs = FileSystem.get(URI.create("s3a://noaa-global-hourly-pds/"), hadoop_conf)

    valid, missing = [], []
    for state, sid, name in stations:
        p = f"s3a://noaa-global-hourly-pds/{year}/{sid}.csv"
        (valid if fs.exists(Path_(p)) else missing).append((state, sid, name))

    if missing:
        print(f"WARNING: {len(missing)} stations NOT found in {year}:")
        for state, sid, name in missing:
            print(f"   {state}  {sid}  {name}")
    print(f"OK: {len(valid)} stations validated\n")

    if not valid:
        raise RuntimeError("No valid station files found")
    return valid


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    spark = (
        SparkSession.builder
        .appName("eda-wind-noaa")
        .config(
            "spark.hadoop.fs.s3a.bucket.noaa-global-hourly-pds.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider",
        )
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    # Disable Arrow — pandas 1.5 + PySpark 3.4 work better without it
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

    valid_stations = validate_stations(spark, YEAR, STATIONS)
    paths = [f"s3a://noaa-global-hourly-pds/{YEAR}/{sid}.csv" for _, sid, _ in valid_stations]

    station_info = spark.createDataFrame(
        [(sid, state, name) for state, sid, name in valid_stations],
        ["STATION", "state", "station_name"],
    )

    print("=" * 70)
    print(f"Reading {YEAR} data for {len(valid_stations)} stations across CA/TX/MN/FL")
    print("=" * 70)

    df_raw = (
        spark.read.option("header", "true").csv(paths)
        .select(
            "STATION", "DATE", "LATITUDE", "LONGITUDE",
            "WND", "TMP", "CIG", "VIS", "DEW", "SLP",
        )
    )

    df = add_parsed_wnd_columns(df_raw)
    df = df.join(station_info, on="STATION", how="left")
    df = df.withColumn("DATE", F.to_timestamp("DATE"))
    df.cache()

    total_rows = df.count()
    print(f"Total rows loaded: {total_rows:,}\n")

    # -------------------------------------------------------------------------
    # Aggregations (Spark) -> small pandas DataFrames
    # -------------------------------------------------------------------------
    metrics = {"year": YEAR, "total_rows": int(total_rows), "n_stations": len(valid_stations)}

    print("Computing data quality metrics...")
    quality = (
        df.groupBy("STATION", "station_name", "state")
        .agg(
            F.count("*").alias("records"),
            F.sum(F.when(F.col("wind_speed_ms").isNull(), 1).otherwise(0)).alias("wind_nulls"),
            F.sum(F.when(F.col("wind_direction_degrees").isNull(), 1).otherwise(0)).alias("dir_nulls"),
            F.min("DATE").alias("first_obs"),
            F.max("DATE").alias("last_obs"),
        )
        .orderBy("state", F.desc("records"))
        .toPandas()
    )
    quality["wind_null_pct"] = (quality["wind_nulls"] / quality["records"] * 100).round(1)
    print(quality[["state", "station_name", "records", "wind_null_pct"]].to_string(index=False))

    print("\nComputing wind speed stats by state...")
    speed_stats = (
        df.filter(F.col("wind_speed_ms").isNotNull())
        .groupBy("state")
        .agg(
            F.count("*").alias("n"),
            F.mean("wind_speed_ms").alias("mean"),
            F.expr("percentile_approx(wind_speed_ms, 0.5)").alias("median"),
            F.expr("percentile_approx(wind_speed_ms, 0.95)").alias("p95"),
            F.max("wind_speed_ms").alias("max"),
            F.stddev("wind_speed_ms").alias("stddev"),
        )
        .orderBy("state")
        .toPandas()
    )
    print(speed_stats.to_string(index=False))

    print("\nSampling wind speeds per state for histograms...")
    sample_speeds = (
        df.filter(F.col("wind_speed_ms").isNotNull() & (F.col("wind_speed_ms") < 50))
        .select("state", "wind_speed_ms")
        .sample(fraction=0.3, seed=42)
        .toPandas()
    )
    print(f"  Sampled {len(sample_speeds):,} rows for plotting")

    print("Computing diurnal cycle (wind speed by hour)...")
    diurnal = (
        df.filter(F.col("wind_speed_ms").isNotNull())
        .withColumn("hour", F.hour("DATE"))
        .groupBy("state", "hour")
        .agg(F.mean("wind_speed_ms").alias("mean_speed"))
        .orderBy("state", "hour")
        .toPandas()
    )

    print("Computing monthly pattern...")
    monthly = (
        df.filter(F.col("wind_speed_ms").isNotNull())
        .withColumn("month", F.month("DATE"))
        .groupBy("state", "month")
        .agg(F.mean("wind_speed_ms").alias("mean_speed"))
        .orderBy("state", "month")
        .toPandas()
    )

    print("Computing wind direction distribution for rose plots...")
    rose = (
        df.filter(
            F.col("wind_speed_ms").isNotNull()
            & F.col("wind_direction_degrees").isNotNull()
            & (F.col("wind_speed_ms") > 0)
        )
        .withColumn("dir_bin", (F.floor(F.col("wind_direction_degrees") / 22.5) * 22.5).cast("int"))
        .withColumn(
            "speed_bucket",
            F.when(F.col("wind_speed_ms") < 2, "0-2")
            .when(F.col("wind_speed_ms") < 5, "2-5")
            .when(F.col("wind_speed_ms") < 10, "5-10")
            .when(F.col("wind_speed_ms") < 15, "10-15")
            .otherwise("15+"),
        )
        .groupBy("state", "dir_bin", "speed_bucket")
        .count()
        .toPandas()
    )

    locations = (
        df.groupBy("STATION", "station_name", "state")
        .agg(F.first("LATITUDE").alias("lat"), F.first("LONGITUDE").alias("lon"))
        .toPandas()
    )
    locations["lat"] = pd.to_numeric(locations["lat"], errors="coerce")
    locations["lon"] = pd.to_numeric(locations["lon"], errors="coerce")

    spark.stop()

    # -------------------------------------------------------------------------
    # PLOTS
    # -------------------------------------------------------------------------
    states = sorted(STATE_COLORS.keys())
    print("\n" + "=" * 70)
    print("Generating plots...")
    print("=" * 70)

    # --- 1. Data quality
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    quality_sorted = quality.sort_values("records", ascending=True)
    colors = [STATE_COLORS[s] for s in quality_sorted["state"]]

    ax1.barh(quality_sorted["station_name"], quality_sorted["records"], color=colors)
    ax1.set_xlabel("Number of records")
    ax1.set_title(f"Records per station — {YEAR}", fontsize=13, fontweight="bold")
    ax1.grid(axis="x", alpha=0.3)

    ax2.barh(quality_sorted["station_name"], quality_sorted["wind_null_pct"], color=colors)
    ax2.set_xlabel("% missing wind speed")
    ax2.set_title("Wind speed null rate", fontsize=13, fontweight="bold")
    ax2.grid(axis="x", alpha=0.3)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in STATE_COLORS.values()]
    fig.legend(handles, STATE_COLORS.keys(), loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02))
    save_fig(fig, "01_data_quality.png")

    # --- 2. Wind speed distribution per state
    fig, axes = plt.subplots(1, 4, figsize=(18, 4), sharey=True)
    for ax, state in zip(axes, states):
        data = sample_speeds[sample_speeds["state"] == state]["wind_speed_ms"]
        ax.hist(data, bins=50, color=STATE_COLORS[state], alpha=0.8, edgecolor="white")
        stats = speed_stats[speed_stats["state"] == state].iloc[0]
        ax.axvline(stats["mean"], color="black", linestyle="--", linewidth=1.5,
                   label=f"mean={stats['mean']:.1f}")
        ax.set_title(f"{state} — μ={stats['mean']:.1f} m/s, p95={stats['p95']:.1f}",
                     fontweight="bold")
        ax.set_xlabel("Wind speed (m/s)")
        ax.set_xlim(0, 25)
        ax.legend()
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Frequency")
    fig.suptitle(f"Wind speed distribution by state — {YEAR}",
                 fontsize=14, fontweight="bold", y=1.02)
    save_fig(fig, "02_wind_speed_dist.png")

    # --- 3. Diurnal cycle
    fig, ax = plt.subplots(figsize=(12, 6))
    for state in states:
        d = diurnal[diurnal["state"] == state]
        ax.plot(d["hour"], d["mean_speed"], marker="o", label=state,
                color=STATE_COLORS[state], linewidth=2)
    ax.set_xlabel("Hour of day (UTC)")
    ax.set_ylabel("Mean wind speed (m/s)")
    ax.set_title(f"Diurnal wind cycle — {YEAR}", fontsize=13, fontweight="bold")
    ax.set_xticks(range(0, 24, 2))
    ax.legend(title="State")
    ax.grid(alpha=0.3)
    save_fig(fig, "03_diurnal_cycle.png")

    # --- 4. Monthly pattern
    fig, ax = plt.subplots(figsize=(12, 6))
    for state in states:
        d = monthly[monthly["state"] == state]
        ax.plot(d["month"], d["mean_speed"], marker="o", label=state,
                color=STATE_COLORS[state], linewidth=2)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean wind speed (m/s)")
    ax.set_title(f"Monthly wind pattern — {YEAR}", fontsize=13, fontweight="bold")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.legend(title="State")
    ax.grid(alpha=0.3)
    save_fig(fig, "04_seasonal.png")

    # --- 5. Wind rose
    fig, axes = plt.subplots(1, 4, figsize=(20, 5), subplot_kw={"projection": "polar"})
    speed_order = ["0-2", "2-5", "5-10", "10-15", "15+"]
    speed_colors = ["#d0e1f9", "#7fb3d5", "#3498db", "#2874a6", "#1a5276"]
    for ax, state in zip(axes, states):
        d = rose[rose["state"] == state]
        if d.empty:
            ax.set_title(f"{state} — no data")
            continue
        pivot = d.pivot_table(index="dir_bin", columns="speed_bucket",
                              values="count", fill_value=0)
        pivot = pivot.reindex(columns=speed_order, fill_value=0)
        theta = np.deg2rad(pivot.index.values)
        width = np.deg2rad(22.5)
        bottom = np.zeros(len(theta))
        for bucket, color in zip(speed_order, speed_colors):
            if bucket in pivot.columns:
                ax.bar(theta, pivot[bucket].values, width=width, bottom=bottom,
                       color=color, edgecolor="white", linewidth=0.5, label=bucket)
                bottom = bottom + pivot[bucket].values
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title(f"{state}", fontsize=13, fontweight="bold", pad=15)
        ax.set_yticklabels([])
    axes[-1].legend(loc="center left", bbox_to_anchor=(1.15, 0.5), title="m/s")
    fig.suptitle(f"Wind rose by state — {YEAR}", fontsize=14, fontweight="bold", y=1.02)
    save_fig(fig, "05_wind_rose.png")

    # --- 6. Station map
    fig, ax = plt.subplots(figsize=(12, 7))
    for state in states:
        d = locations[locations["state"] == state]
        ax.scatter(d["lon"], d["lat"], s=120, c=STATE_COLORS[state], label=state,
                   edgecolor="black", linewidth=0.5, alpha=0.8)
    for _, row in locations.iterrows():
        if pd.notna(row["lat"]) and pd.notna(row["lon"]):
            ax.annotate(row["station_name"].split()[0], (row["lon"], row["lat"]),
                        fontsize=7, xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Station locations — {len(locations)} stations",
                 fontsize=13, fontweight="bold")
    ax.legend(title="State")
    ax.grid(alpha=0.3)
    save_fig(fig, "06_station_map.png")

    # --- Metrics JSON
    metrics["quality"] = quality.to_dict(orient="records")
    metrics["speed_stats"] = speed_stats.to_dict(orient="records")
    with open(METRICS_DIR / "eda_summary.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\n  saved {METRICS_DIR / 'eda_summary.json'}")

    print("\n" + "=" * 70)
    print(f"EDA complete. {len(list(OUTPUT_DIR.glob('*.png')))} plots in {OUTPUT_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()