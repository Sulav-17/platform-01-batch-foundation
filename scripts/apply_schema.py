from pathlib import Path

from ontario_energy_warehouse.database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"


def apply_schema() -> None:
    """Create the warehouse tables in the selected database."""

    schema_text = SCHEMA_FILE.read_text(encoding="utf-8")

    statements = [
        statement.strip()
        for statement in schema_text.split(";")
        if statement.strip()
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

        connection.commit()

    print("Database schema applied successfully.")


if __name__ == "__main__":
    apply_schema()