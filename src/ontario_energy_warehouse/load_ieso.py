import hashlib
from pathlib import Path

import pandas as pd

from ontario_energy_warehouse.database import get_connection
from ontario_energy_warehouse.read_ieso import (
    find_latest_raw_file,
    read_ieso_file,
)
from ontario_energy_warehouse.validate_ieso import validate_ieso_data


def calculate_file_hash(file_path: Path) -> str:
    file_hash = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def load_ieso_data() -> tuple[int, int]:
    source_path = find_latest_raw_file()
    content_hash = calculate_file_hash(source_path)

    connection = get_connection()
    run_id = None
    rows_received = 0

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_runs (
                    source_name,
                    status,
                    source_file,
                    content_hash
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    "ieso_hourly_demand",
                    "running",
                    str(source_path),
                    content_hash,
                ),
            )

            run_id = cursor.fetchone()[0]

        connection.commit()

        data = read_ieso_file()
        rows_received = len(data)

        validate_ieso_data(data)

        upsert_sql = """
            INSERT INTO energy_demand_hourly (
                demand_date,
                hour_ending,
                market_demand_mw,
                ontario_demand_mw,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s)

            ON CONFLICT (demand_date, hour_ending)
            DO UPDATE SET
                market_demand_mw = EXCLUDED.market_demand_mw,
                ontario_demand_mw = EXCLUDED.ontario_demand_mw,
                source_file = EXCLUDED.source_file,
                loaded_at = NOW()

            WHERE
                energy_demand_hourly.market_demand_mw
                    IS DISTINCT FROM EXCLUDED.market_demand_mw
                OR
                energy_demand_hourly.ontario_demand_mw
                    IS DISTINCT FROM EXCLUDED.ontario_demand_mw
        """

        rows_changed = 0

        with connection.cursor() as cursor:
            for _, row in data.iterrows():
                demand_date = pd.to_datetime(row["Date"]).date()

                cursor.execute(
                    upsert_sql,
                    (
                        demand_date,
                        int(row["Hour"]),
                        int(row["Market Demand"]),
                        int(row["Ontario Demand"]),
                        str(source_path),
                    ),
                )

                rows_changed += cursor.rowcount

            cursor.execute(
                """
                UPDATE ingestion_runs
                SET
                    completed_at = NOW(),
                    status = 'completed',
                    rows_received = %s,
                    rows_loaded = %s
                WHERE id = %s
                """,
                (rows_received, rows_changed, run_id),
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
                        rows_received = %s,
                        error_message = %s
                    WHERE id = %s
                    """,
                    (rows_received, str(error), run_id),
                )

            connection.commit()

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    received, changed = load_ieso_data()

    print(f"Rows received: {received}")
    print(f"Rows inserted or updated: {changed}")