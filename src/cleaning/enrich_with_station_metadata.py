# src/cleaning/enrich_with_station_metadata.py

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


STATE_TO_REGION = {
    # Northeast
    "CT": "Northeast",
    "ME": "Northeast",
    "MA": "Northeast",
    "NH": "Northeast",
    "RI": "Northeast",
    "VT": "Northeast",
    "NJ": "Northeast",
    "NY": "Northeast",
    "PA": "Northeast",

    # Midwest
    "IL": "Midwest",
    "IN": "Midwest",
    "MI": "Midwest",
    "OH": "Midwest",
    "WI": "Midwest",
    "IA": "Midwest",
    "KS": "Midwest",
    "MN": "Midwest",
    "MO": "Midwest",
    "NE": "Midwest",
    "ND": "Midwest",
    "SD": "Midwest",

    # South
    "DE": "South",
    "FL": "South",
    "GA": "South",
    "MD": "South",
    "NC": "South",
    "SC": "South",
    "VA": "South",
    "DC": "South",
    "WV": "South",
    "AL": "South",
    "KY": "South",
    "MS": "South",
    "TN": "South",
    "AR": "South",
    "LA": "South",
    "OK": "South",
    "TX": "South",

    # West
    "AZ": "West",
    "CO": "West",
    "ID": "West",
    "MT": "West",
    "NV": "West",
    "NM": "West",
    "UT": "West",
    "WY": "West",
    "AK": "West",
    "CA": "West",
    "HI": "West",
    "OR": "West",
    "WA": "West",
}


def add_us_region_from_state(
    df: DataFrame,
    state_col: str = "state",
    region_col: str = "region",
) -> DataFrame:
    """
    Derive a U.S. census-style region from 2-letter state code.
    """
    if state_col not in df.columns:
        return df

    mapping_expr = F.create_map(
        *[x for kv in STATE_TO_REGION.items() for x in (F.lit(kv[0]), F.lit(kv[1]))]
    )

    return df.withColumn(
        region_col,
        mapping_expr[F.col(state_col)],
    )


def join_station_metadata(
    weather_df: DataFrame,
    station_df: DataFrame,
    station_col: str = "station_id",
) -> DataFrame:
    """
    Left join cleaned weather observations to station metadata on station_id.
    """
    weather_cols = weather_df.columns

    metadata_cols = [
        station_col,
        "station_name",
        "country_code",
        "state",
        "latitude",
        "longitude",
        "elevation_m",
        "begin_date",
        "end_date",
        "begin_year",
        "end_year",
    ]
    metadata_cols = [c for c in metadata_cols if c in station_df.columns]

    station_df_selected = station_df.select(*metadata_cols).dropDuplicates([station_col])

    joined = weather_df.alias("w").join(
        station_df_selected.alias("s"),
        on=station_col,
        how="left",
    )

    ordered_cols = weather_cols + [c for c in station_df_selected.columns if c != station_col]
    return joined.select(*ordered_cols)


def enrich_with_station_metadata(
    weather_df: DataFrame,
    station_df: DataFrame,
    station_col: str = "station_id",
) -> DataFrame:
    """
    Join station metadata and derive region/state-level enrichment fields.
    """
    enriched = join_station_metadata(
        weather_df=weather_df,
        station_df=station_df,
        station_col=station_col,
    )

    enriched = add_us_region_from_state(
        enriched,
        state_col="state",
        region_col="region",
    )

    return enriched