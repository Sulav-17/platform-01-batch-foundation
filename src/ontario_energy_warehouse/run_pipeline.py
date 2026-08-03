from datetime import datetime, timezone

from ontario_energy_warehouse.download_ieso import (
    download_ieso_file,
)
from ontario_energy_warehouse.download_weather import (
    download_weather_backfill,
)
from ontario_energy_warehouse.load_ieso import load_ieso_data
from ontario_energy_warehouse.load_weather import (
    load_weather_data,
)
from ontario_energy_warehouse.raw_storage import (
    cleanup_staging_raw_files,
    using_s3_raw_storage,
)
from ontario_energy_warehouse.s3_storage import (
    stage_raw_files_from_s3,
)


def run_pipeline() -> None:
    started_at = datetime.now(timezone.utc)
    pipeline_succeeded = False

    print("Ontario Energy Warehouse pipeline")
    print(f"Started: {started_at.isoformat()}")
    print()

    try:
        if using_s3_raw_storage():
            print("Preparing raw files from S3...")
            stage_raw_files_from_s3()
            print()

        print("Downloading IESO data...")
        ieso_file = download_ieso_file()
        print(f"IESO raw file ready: {ieso_file}")
        print()

        print("Downloading weather data...")
        download_weather_backfill()
        print("Weather raw files ready")
        print()

        ieso_received, ieso_changed = load_ieso_data()

        print(
            f"IESO complete: {ieso_received} received, "
            f"{ieso_changed} inserted or updated"
        )

        weather_received, weather_changed = load_weather_data()

        print(
            f"Weather complete: {weather_received} received, "
            f"{weather_changed} inserted or updated"
        )

        pipeline_succeeded = True

    finally:
        if pipeline_succeeded:
            cleanup_staging_raw_files()

    completed_at = datetime.now(timezone.utc)
    duration = completed_at - started_at

    print()
    print(f"Completed: {completed_at.isoformat()}")
    print(f"Duration: {duration}")


if __name__ == "__main__":
    run_pipeline()