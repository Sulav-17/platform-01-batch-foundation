from pathlib import Path
from src.ontario_energy_warehouse.validate_ieso import validate_ieso_data
import pandas as pd

from ontario_energy_warehouse.raw_storage import get_raw_root


RAW_DIR = get_raw_root() / "ieso"

EXPECTED_COLUMNS = [
    "Date",
    "Hour",
    "Market Demand",
    "Ontario Demand",
]

def find_latest_raw_file() -> Path:
    """Find the most recently downloaded IESO snapshot."""

    snapshot_files = list(RAW_DIR.glob("PUB_Demand_*.csv"))

    if not snapshot_files:
        raise FileNotFoundError(
            "No IESO snapshot was found. Run the download script first."
        )

    return max(
        snapshot_files,
        key=lambda file_path: file_path.stat().st_mtime,
    )

def read_ieso_file() -> pd.DataFrame:
    """Read the IESO demand file while skipping its metadata rows."""

    raw_file = find_latest_raw_file()
    print(f"Reading: {raw_file}")

    data = pd.read_csv(raw_file, skiprows=3)

    validate_ieso_data(data)

    if list(data.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns: {list(data.columns)}"
        )

    return data

if __name__ == "__main__":
    demand_data = read_ieso_file()

    print(f"Rows: {len(demand_data):,}")
    print(f"Columns: {list(demand_data.columns)}")
    print(f"Date range: {demand_data['Date'].min()} to {demand_data['Date'].max()}")
    print(f"Hour range: {demand_data['Hour'].min()} to {demand_data['Hour'].max()}")
    print(f"Missing values: {demand_data.isna().sum().sum()}")
    print(f"Duplicate rows: {demand_data.duplicated().sum()}")
