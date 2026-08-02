from datetime import date

import pandas as pd

import ontario_energy_warehouse.load_ieso as load_ieso_module
from ontario_energy_warehouse.database import get_connection


TEST_DATE = date(2099, 12, 31)


def remove_test_records(source_file: str) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM energy_demand_hourly
            WHERE demand_date = %s
            """,
            (TEST_DATE,),
        )

        connection.execute(
            """
            DELETE FROM ingestion_runs
            WHERE source_file = %s
            """,
            (source_file,),
        )

        connection.commit()

    finally:
        connection.close()


def test_ieso_loader_inserts_skips_and_updates(
    monkeypatch,
    tmp_path,
):
    raw_file = tmp_path / "test_ieso.csv"
    raw_file.write_text("test file", encoding="utf-8")
    source_file = str(raw_file)

    original_data = pd.DataFrame(
        [
            {
                "Date": TEST_DATE.isoformat(),
                "Hour": 1,
                "Market Demand": 19000,
                "Ontario Demand": 16000,
            }
        ]
    )

    corrected_data = pd.DataFrame(
        [
            {
                "Date": TEST_DATE.isoformat(),
                "Hour": 1,
                "Market Demand": 19050,
                "Ontario Demand": 16025,
            }
        ]
    )

    monkeypatch.setattr(
        load_ieso_module,
        "find_latest_raw_file",
        lambda: raw_file,
    )

    remove_test_records(source_file)

    try:
        monkeypatch.setattr(
            load_ieso_module,
            "read_ieso_file",
            lambda: original_data,
        )

        received, changed = load_ieso_module.load_ieso_data()

        assert received == 1
        assert changed == 1

        received, changed = load_ieso_module.load_ieso_data()

        assert received == 1
        assert changed == 0

        monkeypatch.setattr(
            load_ieso_module,
            "read_ieso_file",
            lambda: corrected_data,
        )

        received, changed = load_ieso_module.load_ieso_data()

        assert received == 1
        assert changed == 1

        connection = get_connection()

        try:
            result = connection.execute(
                """
                SELECT
                    market_demand_mw::INTEGER,
                    ontario_demand_mw::INTEGER
                FROM energy_demand_hourly
                WHERE demand_date = %s
                  AND hour_ending = 1
                """,
                (TEST_DATE,),
            ).fetchone()

            assert result == (19050, 16025)

        finally:
            connection.close()

    finally:
        remove_test_records(source_file)
