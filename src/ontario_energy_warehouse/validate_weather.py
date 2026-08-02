import pandas as pd


REQUIRED_COLUMNS = [
    "station_id",
    "station_name",
    "local_timestamp",
    "utc_timestamp",
]


def validate_weather_data(data: pd.DataFrame) -> None:
    """Validate cleaned hourly weather records."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if data[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("Required weather fields contain missing values.")

    if data["station_name"].astype("string").str.strip().eq("").any():
        raise ValueError("Station name cannot be empty.")

    if data.duplicated(
        subset=["station_id", "utc_timestamp"]
    ).any():
        raise ValueError("Duplicate station and UTC timestamp found.")

    humidity = data["relative_humidity"].dropna()

    if not humidity.between(0, 100).all():
        raise ValueError("Humidity must be between 0 and 100.")

    wind_speed = data["wind_speed"].dropna()

    if not wind_speed.ge(0).all():
        raise ValueError("Wind speed cannot be negative.")

    precipitation = data["precipitation"].dropna()

    if not precipitation.ge(0).all():
        raise ValueError("Precipitation cannot be negative.")