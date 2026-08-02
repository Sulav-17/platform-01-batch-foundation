import hashlib
from pathlib import Path

import pandas as pd

from ontario_energy_warehouse.database import get_connection
from ontario_energy_warehouse.read_weather_history import read_weather_history


def calculate_history_hash(source_files: list[str]) -> str:
    combined_hash = hashlib.sha256()

    for source_file in sorted(source_files):
        combined_hash.update(source_file.encode("utf-8"))

    return combined_hash.hexdigest()


def clean_optional_value(value):
    if pd.isna(value):
        return None

    return value


def load_weather_data() -> tuple[int, int]:
    data = read_weather_history()
    rows_received = len(data)

    source_files = data["source_file"].dropna().unique().tolist()
    content_hash = calculate_history_hash(source_files)

    connection = get_connection()
    run_id = None

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_runs (
                    source_name,
                    status,
                    source_file,
                    content_hash,
                    rows_received
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    "eccc_hourly_weather",
                    "running",
                    f"{len(source_files)} monthly files",
                    content_hash,
                    rows_received,
                ),
            )

            run_id = cursor.fetchone()[0]

        connection.commit()

        upsert_sql = """
            INSERT INTO weather_hourly (
                station_id,
                station_name,
                utc_timestamp,
                local_timestamp,
                temperature_c,
                relative_humidity_pct,
                wind_speed_kmh,
                precipitation_mm,
                weather_description,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            ON CONFLICT (station_id, utc_timestamp)
            DO UPDATE SET
                station_name = EXCLUDED.station_name,
                local_timestamp = EXCLUDED.local_timestamp,
                temperature_c = EXCLUDED.temperature_c,
                relative_humidity_pct = EXCLUDED.relative_humidity_pct,
                wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                precipitation_mm = EXCLUDED.precipitation_mm,
                weather_description = EXCLUDED.weather_description,
                source_file = EXCLUDED.source_file,
                loaded_at = NOW()

            WHERE
                weather_hourly.station_name
                    IS DISTINCT FROM EXCLUDED.station_name
                OR weather_hourly.local_timestamp
                    IS DISTINCT FROM EXCLUDED.local_timestamp
                OR weather_hourly.temperature_c
                    IS DISTINCT FROM EXCLUDED.temperature_c
                OR weather_hourly.relative_humidity_pct
                    IS DISTINCT FROM EXCLUDED.relative_humidity_pct
                OR weather_hourly.wind_speed_kmh
                    IS DISTINCT FROM EXCLUDED.wind_speed_kmh
                OR weather_hourly.precipitation_mm
                    IS DISTINCT FROM EXCLUDED.precipitation_mm
                OR weather_hourly.weather_description
                    IS DISTINCT FROM EXCLUDED.weather_description
        """

        rows_changed = 0

        with connection.cursor() as cursor:
            for _, row in data.iterrows():
                cursor.execute(
                    upsert_sql,
                    (
                        str(row["station_id"]),
                        row["station_name"],
                        row["utc_timestamp"].to_pydatetime(),
                        row["local_timestamp"].to_pydatetime(),
                        clean_optional_value(row["temperature"]),
                        clean_optional_value(row["relative_humidity"]),
                        clean_optional_value(row["wind_speed"]),
                        clean_optional_value(row["precipitation"]),
                        clean_optional_value(row["weather_description"]),
                        row["source_file"],
                    ),
                )

                rows_changed += cursor.rowcount

            cursor.execute(
                """
                UPDATE ingestion_runs
                SET
                    completed_at = NOW(),
                    status = 'completed',
                    rows_loaded = %s
                WHERE id = %s
                """,
                (rows_changed, run_id),
            )

        connection.commit()
        return rows_received, rows_changed

    except Exception as error:
        connection.rollback()

        if run_id is not None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE ingestion_runs
                    SET
                        completed_at = NOW(),
                        status = 'failed',
                        error_message = %s
                    WHERE id = %s
                    """,
                    (str(error), run_id),
                )

            connection.commit()

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    received, changed = load_weather_data()

    print(f"Rows received: {received}")
    print(f"Rows inserted or updated: {changed}")
