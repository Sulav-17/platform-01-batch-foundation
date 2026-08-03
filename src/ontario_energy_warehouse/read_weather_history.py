from pathlib import Path

import pandas as pd

from src.ontario_energy_warehouse.read_weather import (
    read_weather_file,
)
from src.ontario_energy_warehouse.validate_weather_history import (
    validate_weather_completeness,
)
from ontario_energy_warehouse.raw_storage import (
    get_raw_root,
    using_s3_raw_storage,
)
from ontario_energy_warehouse.s3_storage import s3_uri_for_file

RAW_DIR = get_raw_root() / "eccc" / "2026"


def read_weather_history() -> pd.DataFrame:
    """Combine all monthly ECCC weather files."""

    raw_files = sorted(
        RAW_DIR.glob("toronto_city_centre_*.json")
    )

    if not raw_files:
        raise FileNotFoundError("No monthly weather files found.")

    monthly_data = []

    for raw_file in raw_files:
        data = read_weather_file(raw_file)

        if using_s3_raw_storage():
            data["source_file"] = s3_uri_for_file(raw_file)
        else:
            data["source_file"] = raw_file.name

        monthly_data.append(data)

    combined = pd.concat(
        monthly_data,
        ignore_index=True,
    )

    duplicate_count = combined.duplicated(
        subset=["station_id", "utc_timestamp"]
    ).sum()

    combined = (
        combined.sort_values(
            ["utc_timestamp", "source_file"]
        )
        .drop_duplicates(
            subset=["station_id", "utc_timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    print(f"Files read: {len(raw_files)}")
    print(f"Rows after combining: {len(combined):,}")
    print(f"Overlapping records removed: {duplicate_count}")

    missing_hours = validate_weather_completeness(combined)

    print(f"Missing hourly timestamps: {len(missing_hours)}")

    for timestamp in missing_hours:
        print(f"  {timestamp}")

    return combined


if __name__ == "__main__":
    weather_data = read_weather_history()

    print(
        "UTC range: "
        f"{weather_data['utc_timestamp'].min()} to "
        f"{weather_data['utc_timestamp'].max()}"
    )