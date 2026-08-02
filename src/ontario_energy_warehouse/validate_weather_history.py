import warnings

import pandas as pd


MAX_MISSING_HOURS = 5


def find_missing_utc_hours(
    data: pd.DataFrame,
) -> pd.DatetimeIndex:
    """Find gaps between the first and last weather timestamps."""

    if data.empty:
        raise ValueError("Weather history contains no records.")

    timestamps = pd.to_datetime(
        data["utc_timestamp"],
        errors="coerce",
        utc=True,
    )

    if timestamps.isna().any():
        raise ValueError("Weather history contains invalid timestamps.")

    expected_hours = pd.date_range(
        start=timestamps.min(),
        end=timestamps.max(),
        freq="h",
    )

    return expected_hours.difference(
        pd.DatetimeIndex(timestamps)
    )


def validate_weather_completeness(
    data: pd.DataFrame,
    max_missing_hours: int = MAX_MISSING_HOURS,
) -> pd.DatetimeIndex:
    """Warn about small gaps and reject excessive gaps."""

    missing_hours = find_missing_utc_hours(data)
    missing_count = len(missing_hours)

    if missing_count > max_missing_hours:
        raise ValueError(
            f"Weather history has {missing_count} missing hours. "
            f"Maximum allowed is {max_missing_hours}."
        )

    if missing_count > 0:
        warnings.warn(
            f"Weather history has {missing_count} missing hours.",
            UserWarning,
            stacklevel=2,
        )

    return missing_hours