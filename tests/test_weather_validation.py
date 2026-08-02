import pandas as pd
import pytest

from src.ontario_energy_warehouse.validate_weather import (
    validate_weather_data,
)


def make_valid_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "station_id": [48549, 48549],
            "station_name": [
                "TORONTO CITY CENTRE",
                "TORONTO CITY CENTRE",
            ],
            "local_timestamp": pd.to_datetime(
                [
                    "2026-01-01 01:00:00",
                    "2026-01-01 02:00:00",
                ]
            ),
            "utc_timestamp": pd.to_datetime(
                [
                    "2026-01-01 06:00:00",
                    "2026-01-01 07:00:00",
                ],
                utc=True,
            ),
            "temperature": [-10.0, -10.5],
            "relative_humidity": [69, 72],
            "wind_speed": [18, 15],
            "precipitation": [0, 0],
            "weather_description": [pd.NA, pd.NA],
        }
    )


def test_valid_weather_data_passes() -> None:
    validate_weather_data(make_valid_data())


def test_invalid_humidity_fails() -> None:
    data = make_valid_data()
    data.loc[0, "relative_humidity"] = 101

    with pytest.raises(ValueError, match="Humidity"):
        validate_weather_data(data)


def test_duplicate_weather_record_fails() -> None:
    data = make_valid_data()
    data.loc[1, "utc_timestamp"] = data.loc[0, "utc_timestamp"]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_weather_data(data)


def test_missing_required_value_fails() -> None:
    data = make_valid_data()
    data.loc[0, "station_name"] = None

    with pytest.raises(ValueError, match="Required"):
        validate_weather_data(data)