"""
Integration module for parsing NOAA ISD core encoded weather fields.

This module applies all field-level parser transformations in sequence:

- WND
- TMP
- DEW
- SLP
- VIS
- CIG

The result is a Spark DataFrame that retains the original encoded columns
and appends parsed weather columns for downstream cleaning and validation.
"""

from __future__ import annotations

from pyspark.sql import DataFrame

from src.parsing.parse_cig import add_parsed_cig_columns
from src.parsing.parse_dew import add_parsed_dew_columns
from src.parsing.parse_slp import add_parsed_slp_columns
from src.parsing.parse_tmp import add_parsed_tmp_columns
from src.parsing.parse_vis import add_parsed_vis_columns
from src.parsing.parse_wnd import add_parsed_wnd_columns


CORE_PARSE_SOURCE_COLUMNS = ("WND", "TMP", "DEW", "SLP", "VIS", "CIG")


def add_all_parsed_weather_columns(df: DataFrame) -> DataFrame:
    """
    Apply all NOAA ISD core field parsers to a Spark DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input Spark DataFrame containing the raw encoded NOAA ISD columns.

    Returns
    -------
    DataFrame
        Spark DataFrame with all parsed weather columns appended.

    Notes
    -----
    Expected raw source columns:
    - WND
    - TMP
    - DEW
    - SLP
    - VIS
    - CIG

    This function preserves the original raw columns and adds parsed columns.
    """
    missing_cols = [col_name for col_name in CORE_PARSE_SOURCE_COLUMNS if col_name not in df.columns]
    if missing_cols:
        raise KeyError(
            "Missing required raw NOAA ISD columns for parsing: "
            + ", ".join(missing_cols)
        )

    result = df
    result = add_parsed_wnd_columns(result, source_col="WND")
    result = add_parsed_tmp_columns(result, source_col="TMP")
    result = add_parsed_dew_columns(result, source_col="DEW")
    result = add_parsed_slp_columns(result, source_col="SLP")
    result = add_parsed_vis_columns(result, source_col="VIS")
    result = add_parsed_cig_columns(result, source_col="CIG")

    return result