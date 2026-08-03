import os
import shutil
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = os.getenv("ENV_FILE", ".env")

load_dotenv(PROJECT_ROOT / ENV_FILE, override=True)

LOCAL_RAW_ROOT = PROJECT_ROOT / "data" / "raw"
STAGING_RAW_ROOT = PROJECT_ROOT / "data" / "staging" / "raw"


def get_raw_storage_mode() -> str:
    """Return either local or s3 raw-storage mode."""

    mode = os.getenv("RAW_STORAGE_MODE", "local").strip().lower()

    if mode not in {"local", "s3"}:
        raise RuntimeError(
            "RAW_STORAGE_MODE must be either 'local' or 's3'."
        )

    return mode


def using_s3_raw_storage() -> bool:
    return get_raw_storage_mode() == "s3"


def get_raw_root() -> Path:
    """Return the active raw-file folder."""

    if using_s3_raw_storage():
        return STAGING_RAW_ROOT

    return LOCAL_RAW_ROOT


def cleanup_staging_raw_files() -> None:
    """Remove temporary AWS-mode files after a successful pipeline."""

    if not using_s3_raw_storage():
        return

    if STAGING_RAW_ROOT.exists():
        shutil.rmtree(STAGING_RAW_ROOT)

    print("Temporary raw staging files removed.")