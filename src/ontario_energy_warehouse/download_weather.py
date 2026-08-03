from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import requests

from ontario_energy_warehouse.s3_storage import upload_raw_file

API_URL = (
    "https://api.weather.gc.ca/"
    "collections/climate-hourly/items"
)

STATION_ID = 48549
START_DATE = date(2026, 1, 1)
RAW_DIR = Path("data/raw/eccc")


def create_month_ranges(
    start_date: date,
    end_date: date,
) -> list[tuple[date, date]]:
    """Split a date range into monthly sections."""

    ranges = []
    current_date = start_date

    while current_date <= end_date:
        last_day = monthrange(
            current_date.year,
            current_date.month,
        )[1]

        month_end = date(
            current_date.year,
            current_date.month,
            last_day,
        )

        range_end = min(month_end, end_date)

        ranges.append((current_date, range_end))

        current_date = range_end + timedelta(days=1)

    return ranges


def download_weather_month(
    start_date: date,
    end_date: date,
) -> Path:
    """Download and preserve one monthly weather response."""

    params = {
        "f": "json",
        "STN_ID": STATION_ID,
        "datetime": (
            f"{start_date.isoformat()}/"
            f"{end_date.isoformat()}"
        ),
        "limit": 10000,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60,
    )
    response.raise_for_status()

    payload = response.json()
    records = payload.get("features", [])

    if not records:
        raise ValueError(
            f"No weather records returned for "
            f"{start_date} to {end_date}."
        )

    file_content = response.content
    content_hash = sha256(file_content).hexdigest()[:12]

    year_dir = RAW_DIR / str(start_date.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    range_name = (
        f"{start_date.isoformat()}_to_"
        f"{end_date.isoformat()}"
    )

    existing_files = list(
        year_dir.glob(
            f"toronto_city_centre_{range_name}_*_{content_hash}.json"
        )
    )

    if existing_files:
        existing_file = existing_files[0]

        print(
            f"Already downloaded: "
            f"{start_date} to {end_date}"
        )

        upload_raw_file(existing_file)

        return existing_file

    downloaded_at = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    file_path = year_dir / (
        f"toronto_city_centre_{range_name}_"
        f"{downloaded_at}_{content_hash}.json"
    )

    file_path.write_bytes(file_content)

    upload_raw_file(file_path)

    print(
        f"Saved {len(records):,} records: "
        f"{start_date} to {end_date}"
    )

    return file_path


def download_weather_backfill() -> None:
    """Download weather from January 1 through yesterday."""

    end_date = date.today() - timedelta(days=1)

    month_ranges = create_month_ranges(
        START_DATE,
        end_date,
    )

    for start_date, range_end in month_ranges:
        download_weather_month(start_date, range_end)


if __name__ == "__main__":
    download_weather_backfill()