import pandas as pd
import pytest

from src.ontario_energy_warehouse.validate_weather_history import (
    validate_weather_completeness,
)


def make_history(
    timestamps: list[str],
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "utc_timestamp": pd.to_datetime(
                timestamps,
                utc=True,
            )
        }
    )


def test_complete_history_passes() -> None:
    data = make_history(
        [
            "2026-01-01 00:00:00",
            "2026-01-01 01:00:00",
            "2026-01-01 02:00:00",
        ]
    )

    missing = validate_weather_completeness(data)

    assert len(missing) == 0


def test_small_gap_creates_warning() -> None:
    data = make_history(
        [
            "2026-01-01 00:00:00",
            "2026-01-01 02:00:00",
        ]
    )

    with pytest.warns(UserWarning, match="1 missing"):
        missing = validate_weather_completeness(data)

    assert len(missing) == 1


def test_more_than_five_gaps_fails() -> None:
    data = make_history(
        [
            "2026-01-01 00:00:00",
            "2026-01-01 07:00:00",
        ]
    )

    with pytest.raises(ValueError, match="6 missing"):
        validate_weather_completeness(data)