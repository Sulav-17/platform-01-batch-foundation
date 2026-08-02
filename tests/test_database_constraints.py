from datetime import date, datetime, timezone

import psycopg
import pytest

from ontario_energy_warehouse.database import get_connection


@pytest.fixture
def database_connection():
    connection = get_connection()

    yield connection

    connection.rollback()
    connection.close()


def test_expected_tables_exist(database_connection):
    table_names = [
        "ingestion_runs",
        "energy_demand_hourly",
        "weather_hourly",
    ]

    for table_name in table_names:
        result = database_connection.execute(
            "SELECT to_regclass(%s)",
            (f"public.{table_name}",),
        ).fetchone()

        assert result[0] == table_name


def test_energy_duplicate_key_is_rejected(database_connection):
    row = (
        date(2099, 1, 1),
        1,
        19000,
        16000,
        "test_file.csv",
    )

    insert_sql = """
        INSERT INTO energy_demand_hourly (
            demand_date,
            hour_ending,
            market_demand_mw,
            ontario_demand_mw,
            source_file
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    database_connection.execute(insert_sql, row)

    with pytest.raises(psycopg.errors.UniqueViolation):
        database_connection.execute(insert_sql, row)


def test_invalid_energy_hour_is_rejected(database_connection):
    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO energy_demand_hourly (
                demand_date,
                hour_ending,
                market_demand_mw,
                ontario_demand_mw,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                date(2099, 1, 2),
                25,
                19000,
                16000,
                "test_file.csv",
            ),
        )


def test_invalid_humidity_is_rejected(database_connection):
    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO weather_hourly (
                station_id,
                station_name,
                utc_timestamp,
                local_timestamp,
                relative_humidity_pct,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                "test_station",
                "TEST STATION",
                datetime(2099, 1, 1, tzinfo=timezone.utc),
                datetime(2099, 1, 1),
                101,
                "test_file.json",
            ),
        )
