from __future__ import annotations

import pytest

from src.common.spark_utils import get_local_spark_session, stop_spark_session
from src.parsing.parse_all_fields import add_all_parsed_weather_columns
from src.parsing.parse_cig import add_parsed_cig_columns
from src.parsing.parse_dew import add_parsed_dew_columns
from src.parsing.parse_slp import add_parsed_slp_columns
from src.parsing.parse_tmp import add_parsed_tmp_columns
from src.parsing.parse_vis import add_parsed_vis_columns
from src.parsing.parse_wnd import add_parsed_wnd_columns


@pytest.fixture(scope="module")
def spark():
    spark_session = get_local_spark_session("test-parsers")
    yield spark_session
    stop_spark_session(spark_session)


def test_parse_wnd_valid_and_sentinel_cases(spark):
    df = spark.createDataFrame(
        [
            ("324,1,H,0051,1",),
            ("999,1,H,9999,1",),
            (None,),
            ("bad,data",),
        ],
        ["WND"],
    )

    result = add_parsed_wnd_columns(df).collect()

    assert result[0]["wind_direction_degrees"] == 324
    assert result[0]["wind_direction_qc"] == "1"
    assert result[0]["wind_observation_type"] == "H"
    assert result[0]["wind_speed_ms"] == pytest.approx(5.1)
    assert result[0]["wind_speed_qc"] == "1"

    assert result[1]["wind_direction_degrees"] is None
    assert result[1]["wind_speed_ms"] is None
    assert result[1]["wind_direction_qc"] == "1"
    assert result[1]["wind_speed_qc"] == "1"

    assert result[2]["wind_direction_degrees"] is None
    assert result[2]["wind_speed_ms"] is None
    assert result[2]["wind_direction_qc"] is None
    assert result[2]["wind_speed_qc"] is None

    assert result[3]["wind_direction_degrees"] is None
    assert result[3]["wind_speed_ms"] is None
    assert result[3]["wind_direction_qc"] is None
    assert result[3]["wind_speed_qc"] is None


def test_parse_tmp_valid_sentinel_and_malformed_cases(spark):
    df = spark.createDataFrame(
        [
            ("+0093,1",),
            ("-0050,1",),
            ("+9999,1",),
            ("-9999,1",),
            (None,),
            ("bad,data",),
        ],
        ["TMP"],
    )

    result = add_parsed_tmp_columns(df).collect()

    assert float(result[0]["temperature_c"]) == pytest.approx(9.3)
    assert result[0]["temperature_qc"] == "1"

    assert float(result[1]["temperature_c"]) == pytest.approx(-5.0)
    assert result[1]["temperature_qc"] == "1"

    assert result[2]["temperature_c"] is None
    assert result[2]["temperature_qc"] == "1"

    assert result[3]["temperature_c"] is None
    assert result[3]["temperature_qc"] == "1"

    assert result[4]["temperature_c"] is None
    assert result[4]["temperature_qc"] is None

    assert result[5]["temperature_c"] is None
    assert result[5]["temperature_qc"] == "data"


def test_parse_dew_valid_sentinel_and_malformed_cases(spark):
    df = spark.createDataFrame(
        [
            ("+0078,1",),
            ("-0123,1",),
            ("+9999,1",),
            ("-9999,1",),
            (None,),
            ("bad,data",),
        ],
        ["DEW"],
    )

    result = add_parsed_dew_columns(df).collect()

    assert float(result[0]["dew_point_c"]) == pytest.approx(7.8)
    assert result[0]["dew_point_qc"] == "1"

    assert float(result[1]["dew_point_c"]) == pytest.approx(-12.3)
    assert result[1]["dew_point_qc"] == "1"

    assert result[2]["dew_point_c"] is None
    assert result[2]["dew_point_qc"] == "1"

    assert result[3]["dew_point_c"] is None
    assert result[3]["dew_point_qc"] == "1"

    assert result[4]["dew_point_c"] is None
    assert result[4]["dew_point_qc"] is None

    assert result[5]["dew_point_c"] is None
    assert result[5]["dew_point_qc"] == "data"


def test_parse_slp_valid_sentinel_and_malformed_cases(spark):
    df = spark.createDataFrame(
        [
            ("10132,1",),
            ("09987,1",),
            ("99999,1",),
            (None,),
            ("bad,data",),
        ],
        ["SLP"],
    )

    result = add_parsed_slp_columns(df).collect()

    assert float(result[0]["sea_level_pressure_hpa"]) == pytest.approx(1013.2)
    assert result[0]["sea_level_pressure_qc"] == "1"

    assert float(result[1]["sea_level_pressure_hpa"]) == pytest.approx(998.7)
    assert result[1]["sea_level_pressure_qc"] == "1"

    assert result[2]["sea_level_pressure_hpa"] is None
    assert result[2]["sea_level_pressure_qc"] == "1"

    assert result[3]["sea_level_pressure_hpa"] is None
    assert result[3]["sea_level_pressure_qc"] is None

    assert result[4]["sea_level_pressure_hpa"] is None
    assert result[4]["sea_level_pressure_qc"] == "data"


def test_parse_vis_valid_sentinel_and_malformed_cases(spark):
    df = spark.createDataFrame(
        [
            ("016093,1,N,1",),
            ("000800,1,V,1",),
            ("999999,1,9,1",),
            (None,),
            ("bad,data",),
        ],
        ["VIS"],
    )

    result = add_parsed_vis_columns(df).collect()

    assert result[0]["visibility_distance_m"] == pytest.approx(16093.0)
    assert result[0]["visibility_distance_qc"] == "1"
    assert result[0]["visibility_variability"] == "N"
    assert result[0]["visibility_variability_qc"] == "1"

    assert result[1]["visibility_distance_m"] == pytest.approx(800.0)
    assert result[1]["visibility_distance_qc"] == "1"
    assert result[1]["visibility_variability"] == "V"
    assert result[1]["visibility_variability_qc"] == "1"

    assert result[2]["visibility_distance_m"] is None
    assert result[2]["visibility_distance_qc"] == "1"
    assert result[2]["visibility_variability"] == "9"
    assert result[2]["visibility_variability_qc"] == "1"

    assert result[3]["visibility_distance_m"] is None
    assert result[3]["visibility_distance_qc"] is None
    assert result[3]["visibility_variability"] is None
    assert result[3]["visibility_variability_qc"] is None

    assert result[4]["visibility_distance_m"] is None
    assert result[4]["visibility_distance_qc"] is None
    assert result[4]["visibility_variability"] is None
    assert result[4]["visibility_variability_qc"] is None


def test_parse_cig_valid_sentinel_and_malformed_cases(spark):
    df = spark.createDataFrame(
        [
            ("02200,1,5,0",),
            ("00050,1,7,0",),
            ("99999,1,9,9",),
            (None,),
            ("bad,data",),
        ],
        ["CIG"],
    )

    result = add_parsed_cig_columns(df).collect()

    assert result[0]["ceiling_height_m"] == pytest.approx(2200.0)
    assert result[0]["ceiling_height_qc"] == "1"
    assert result[0]["ceiling_determination_code"] == "5"
    assert result[0]["ceiling_cavok"] == "0"

    assert result[1]["ceiling_height_m"] == pytest.approx(50.0)
    assert result[1]["ceiling_height_qc"] == "1"
    assert result[1]["ceiling_determination_code"] == "7"
    assert result[1]["ceiling_cavok"] == "0"

    assert result[2]["ceiling_height_m"] is None
    assert result[2]["ceiling_height_qc"] == "1"
    assert result[2]["ceiling_determination_code"] == "9"
    assert result[2]["ceiling_cavok"] == "9"

    assert result[3]["ceiling_height_m"] is None
    assert result[3]["ceiling_height_qc"] is None
    assert result[3]["ceiling_determination_code"] is None
    assert result[3]["ceiling_cavok"] is None

    assert result[4]["ceiling_height_m"] is None
    assert result[4]["ceiling_height_qc"] is None
    assert result[4]["ceiling_determination_code"] is None
    assert result[4]["ceiling_cavok"] is None


def test_parse_all_fields_integration(spark):
    df = spark.createDataFrame(
        [
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
        ],
        ["WND", "TMP", "DEW", "SLP", "VIS", "CIG"],
    )

    result = add_all_parsed_weather_columns(df).collect()

    assert result[0]["wind_direction_degrees"] == 324
    assert result[0]["wind_speed_ms"] == pytest.approx(5.1)
    assert float(result[0]["temperature_c"]) == pytest.approx(9.3)
    assert float(result[0]["dew_point_c"]) == pytest.approx(7.8)
    assert float(result[0]["sea_level_pressure_hpa"]) == pytest.approx(1013.2)
    assert result[0]["visibility_distance_m"] == pytest.approx(16093.0)
    assert result[0]["ceiling_height_m"] == pytest.approx(2200.0)

    assert result[1]["wind_direction_degrees"] is None
    assert result[1]["wind_speed_ms"] is None
    assert result[1]["temperature_c"] is None
    assert result[1]["dew_point_c"] is None
    assert result[1]["sea_level_pressure_hpa"] is None
    assert result[1]["visibility_distance_m"] is None
    assert result[1]["ceiling_height_m"] is None


def test_parse_all_fields_raises_on_missing_required_columns(spark):
    df = spark.createDataFrame(
        [
            ("324,1,H,0051,1", "+0093,1"),
        ],
        ["WND", "TMP"],
    )

    with pytest.raises(KeyError):
        add_all_parsed_weather_columns(df)