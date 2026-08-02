from datetime import datetime, timezone

from ontario_energy_warehouse.load_ieso import load_ieso_data
from ontario_energy_warehouse.load_weather import load_weather_data


def run_pipeline() -> None:
    started_at = datetime.now(timezone.utc)

    print("Ontario Energy Warehouse pipeline")
    print(f"Started: {started_at.isoformat()}")
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

    completed_at = datetime.now(timezone.utc)
    duration = completed_at - started_at

    print()
    print(f"Completed: {completed_at.isoformat()}")
    print(f"Duration: {duration}")


if __name__ == "__main__":
    run_pipeline()
