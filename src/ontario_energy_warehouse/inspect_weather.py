import json
from pathlib import Path

import pandas as pd


RAW_FILE = Path(
    "data/raw/eccc/"
    "toronto_city_centre_2026-01-01.json"
)

SELECTED_FIELDS = [
    "STN_ID",
    "STATION_NAME",
    "LOCAL_DATE",
    "UTC_DATE",
    "TEMP",
    "RELATIVE_HUMIDITY",
    "WIND_SPEED",
    "PRECIP_AMOUNT",
    "WEATHER_ENG_DESC",
]


def inspect_weather_file() -> None:
    """Inspect the weather fields we may load later."""

    with RAW_FILE.open(encoding="utf-8") as file:
        payload = json.load(file)

    records = [
        feature["properties"]
        for feature in payload["features"]
    ]

    data = pd.DataFrame(records)[SELECTED_FIELDS]

    print(f"Rows: {len(data):,}")
    print("\nMissing values:")
    print(data.isna().sum())

    print("\nFirst five records:")
    print(data.head().to_string(index=False))


if __name__ == "__main__":
    inspect_weather_file()