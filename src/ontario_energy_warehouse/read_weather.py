import json
from pathlib import Path

import pandas as pd

from src.ontario_energy_warehouse.validate_weather import (
    validate_weather_data,
)


RAW_FILE = Path(
    "data/raw/eccc/"
    "toronto_city_centre_2026-01-01.json"
)

FIELD_MAP = {
    "STN_ID": "station_id",
    "STATION_NAME": "station_name",
    "LOCAL_DATE": "local_timestamp",
    "UTC_DATE": "utc_timestamp",
    "TEMP": "temperature",
    "RELATIVE_HUMIDITY": "relative_humidity",
    "WIND_SPEED": "wind_speed",
    "PRECIP_AMOUNT": "precipitation",
    "WEATHER_ENG_DESC": "weather_description",
}


def read_weather_file(
    raw_file: Path = RAW_FILE,
) -> pd.DataFrame:
    """Read, clean, validate, and sort ECCC weather data."""

    with raw_file.open(encoding="utf-8") as file:
        payload = json.load(file)

    features = payload.get("features", [])

    if not features:
        raise ValueError("The weather file contains no records.")

    records = [
        feature.get("properties", {})
        for feature in features
    ]

    data = pd.DataFrame(records)

    missing_fields = [
        field
        for field in FIELD_MAP
        if field not in data.columns
    ]

    if missing_fields:
        raise ValueError(
            f"Source fields are missing: {missing_fields}"
        )

    data = data[list(FIELD_MAP)].rename(columns=FIELD_MAP)

    data["weather_description"] = (
        data["weather_description"]
        .replace({"NA": pd.NA, "": pd.NA})
    )

    data["station_id"] = pd.to_numeric(
        data["station_id"],
        errors="coerce",
    ).astype("Int64")

    data["local_timestamp"] = pd.to_datetime(
        data["local_timestamp"],
        errors="coerce",
    )

    data["utc_timestamp"] = pd.to_datetime(
        data["utc_timestamp"],
        errors="coerce",
        utc=True,
    )

    numeric_columns = [
        "temperature",
        "relative_humidity",
        "wind_speed",
        "precipitation",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    validate_weather_data(data)

    return (
        data.sort_values("utc_timestamp")
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    weather_data = read_weather_file()

    print(f"Rows: {len(weather_data):,}")
    print(
        "UTC range: "
        f"{weather_data['utc_timestamp'].min()} to "
        f"{weather_data['utc_timestamp'].max()}"
    )
    print("\nMissing values:")
    print(weather_data.isna().sum())

    print("\nFirst five sorted records:")
    print(weather_data.head().to_string(index=False))