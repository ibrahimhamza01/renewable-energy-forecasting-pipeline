import pandas as pd

from src.ingestion.station_metadata_loader import load_station_metadata

EXCLUDED_STATES = {
    "AK",  # Alaska
    "HI",  # Hawaii
    "PR",  # Puerto Rico
    "GU",  # Guam
    "VI",  # Virgin Islands
    "AS",  # American Samoa
    "MP",  # Northern Mariana Islands
}

LAT_MIN = 24.5
LAT_MAX = 49.5
LON_MIN = -125.0
LON_MAX = -66.0


def filter_us_stations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["country_code"] == "US"].copy()

def filter_known_states(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["state"].fillna("").str.strip() != ""].copy()

def remove_invalid_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        df["latitude"].notna()
        & df["longitude"].notna()
        & (df["latitude"] != 0)
        & (df["longitude"] != 0)
    ].copy()


def filter_excluded_states(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["state"].isin(EXCLUDED_STATES)].copy()


def filter_contiguous_us_geography(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        (df["latitude"] >= LAT_MIN)
        & (df["latitude"] <= LAT_MAX)
        & (df["longitude"] >= LON_MIN)
        & (df["longitude"] <= LON_MAX)
    ].copy()


def filter_active_stations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["begin_year"].notna() & df["end_year"].notna()].copy()


def build_station_master(df: pd.DataFrame) -> pd.DataFrame:
    df = filter_us_stations(df)
    df = remove_invalid_coordinates(df)
    df = filter_excluded_states(df)
    df = filter_contiguous_us_geography(df)
    df = filter_known_states(df)
    df = filter_active_stations(df)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = load_station_metadata("data/raw/noaa_metadata/isd-history.csv")

    print(f"Total stations: {len(df)}")

    us_df = filter_us_stations(df)
    print(f"US stations: {len(us_df)}")

    coords_df = remove_invalid_coordinates(us_df)
    print(f"After removing invalid coords: {len(coords_df)}")

    states_df = filter_excluded_states(coords_df)
    print(f"After excluding AK/HI/territories: {len(states_df)}")

    contiguous_df = filter_contiguous_us_geography(states_df)
    print(f"Contiguous US stations: {len(contiguous_df)}")

    final_df = filter_active_stations(contiguous_df)
    print(f"Final station master: {len(final_df)}")

    print("\nSample:")
    print(final_df.head(10).to_string(index=False))