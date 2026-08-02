import hashlib
from datetime import datetime, timezone

import pandas as pd

import ontario_energy_warehouse.load_weather as load_weather_module
from ontario_energy_warehouse.database import get_connection


TEST_STATION_ID = "99999"
TEST_UTC_TIME = datetime(2099, 12, 31, 5, tzinfo=timezone.utc)


def calculate_test_hash(source_file: str) -> str:
    history_hash = hashlib.sha256()
    history_hash.update(source_file.encode("utf-8"))
    return history_hash.hexdigest()


def remove_test_records(content_hash: str) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM weather_hourly
            WHERE station_id = %s
              AND utc_timestamp = %s
            """,
            (TEST_STATION_ID, TEST_UTC_TIME),
        )

        connection.execute(
            """
            DELETE FROM ingestion_runs
            WHERE content_hash = %s
            """,
            (content_hash,),
        )

        connection.commit()

    finally:
        connection.close()


def test_weather_loader_inserts_skips_and_updates(
    monkeypatch,
    tmp_path,
):
    source_file = str(tmp_path / "test_weather.json")
    content_hash = calculate_test_hash(source_file)

    original_data = pd.DataFrame(
        [
            {
                "station_id": 99999,
                "station_name": "TEST STATION",
                "local_timestamp": pd.Timestamp(
                    "2099-12-31 00:00:00"
                ),
                "utc_timestamp": pd.Timestamp(
                    "2099-12-31 05:00:00",
                    tz="UTC",
                ),
                "temperature": 5.0,
                "relative_humidity": 70,
                "wind_speed": 10,
                "precipitation": 0.0,
                "weather_description": "Clear",
                "source_file": source_file,
            }
        ]
    )

    corrected_data = original_data.copy()
    corrected_data.loc[0, "temperature"] = 6.5
    corrected_data.loc[0, "weather_description"] = "Cloudy"

    remove_test_records(content_hash)

    try:
        monkeypatch.setattr(
            load_weather_module,
            "read_weather_history",
            lambda: original_data,
        )

        received, changed = load_weather_module.load_weather_data()

        assert received == 1
        assert changed == 1

        received, changed = load_weather_module.load_weather_data()

        assert received == 1
        assert changed == 0

        monkeypatch.setattr(
            load_weather_module,
            "read_weather_history",
            lambda: corrected_data,
        )

        received, changed = load_weather_module.load_weather_data()

        assert received == 1
        assert changed == 1

        connection = get_connection()

        try:
            result = connection.execute(
                """
                SELECT
                    temperature_c,
                    weather_description
                FROM weather_hourly
                WHERE station_id = %s
                  AND utc_timestamp = %s
                """,
                (TEST_STATION_ID, TEST_UTC_TIME),
            ).fetchone()

            assert float(result[0]) == 6.5
            assert result[1] == "Cloudy"

        finally:
            connection.close()

    finally:
        remove_test_records(content_hash)
