from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import requests

IESO_URL = "https://reports-public.ieso.ca/public/Demand/PUB_Demand.csv"
RAW_DIR = Path("data/raw/ieso")

def download_ieso_file() -> Path:
    """Download a new IESO snapshot only when its content has changed."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.get(IESO_URL, timeout=30)
    response.raise_for_status()

    file_content = response.content
    content_hash = sha256(file_content).hexdigest()[:12]

    existing_files = list(
        RAW_DIR.glob(f"PUB_Demand_*_{content_hash}.csv")
    )

    if existing_files:
        print(f"No new snapshot. Existing file: {existing_files[0]}")
        return existing_files[0]

    downloaded_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    snapshot_path = (
        RAW_DIR
        / f"PUB_Demand_{downloaded_at}_{content_hash}.csv"
    )

    snapshot_path.write_bytes(file_content)

    print(f"New snapshot saved: {snapshot_path}")
    print(f"File size: {snapshot_path.stat().st_size:,} bytes")

    return snapshot_path


if __name__ == "__main__":
    download_ieso_file()