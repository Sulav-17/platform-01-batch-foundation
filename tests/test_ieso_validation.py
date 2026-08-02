import pandas as pd
import pytest

from src.ontario_energy_warehouse.validate_ieso import validate_ieso_data


def make_valid_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2026-01-01", "2026-01-01"],
            "Hour": [1, 2],
            "Market Demand": [19489, 19317],
            "Ontario Demand": [16526, 16374],
        }
    )

def test_valid_data_passes() -> None:
    data = make_valid_data()

    validate_ieso_data(data)


def test_invalid_hour_fails() -> None:
    data = make_valid_data()
    data.loc[0, "Hour"] = 25

    with pytest.raises(ValueError, match="Hours"):
        validate_ieso_data(data)


def test_duplicate_date_and_hour_fails() -> None:
    data = make_valid_data()
    data.loc[1, "Hour"] = 1

    with pytest.raises(ValueError, match="Duplicate"):
        validate_ieso_data(data)