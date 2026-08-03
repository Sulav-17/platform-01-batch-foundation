import os
import shutil
from pathlib import Path, PurePosixPath

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from ontario_energy_warehouse.raw_storage import (
    PROJECT_ROOT,
    get_raw_root,
    using_s3_raw_storage,
)


ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(PROJECT_ROOT / ENV_FILE, override=True)

RAW_ROOT = get_raw_root()


def _get_bucket_name() -> str:
    bucket_name = os.getenv("S3_RAW_BUCKET")

    if not bucket_name:
        raise RuntimeError("S3_RAW_BUCKET is missing.")

    return bucket_name


def _get_s3_client():
    session_options = {}

    aws_profile = os.getenv("AWS_PROFILE")
    aws_region = os.getenv("AWS_REGION")

    if aws_profile:
        session_options["profile_name"] = aws_profile

    if aws_region:
        session_options["region_name"] = aws_region

    session = boto3.Session(**session_options)

    return session.client("s3")


def _resolve_raw_file(file_path: Path) -> tuple[Path, Path]:
    absolute_path = Path(file_path)

    if not absolute_path.is_absolute():
        absolute_path = PROJECT_ROOT / absolute_path

    absolute_path = absolute_path.resolve()
    raw_root = RAW_ROOT.resolve()

    if not absolute_path.exists():
        raise FileNotFoundError(
            f"Raw file does not exist: {absolute_path}"
        )

    try:
        relative_path = absolute_path.relative_to(raw_root)
    except ValueError as error:
        raise ValueError(
            f"File must be inside {raw_root}: {absolute_path}"
        ) from error

    return absolute_path, relative_path


def s3_key_for_file(file_path: Path) -> str:
    """Build the permanent S3 key for a staged raw file."""

    _, relative_path = _resolve_raw_file(file_path)

    return f"raw/{relative_path.as_posix()}"


def s3_uri_for_file(file_path: Path) -> str:
    bucket_name = _get_bucket_name()
    s3_key = s3_key_for_file(file_path)

    return f"s3://{bucket_name}/{s3_key}"


def stage_raw_files_from_s3() -> int:
    """Download permanent S3 raw files into temporary staging."""

    if not using_s3_raw_storage():
        return 0

    bucket_name = _get_bucket_name()
    s3_client = _get_s3_client()

    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)

    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    paginator = s3_client.get_paginator("list_objects_v2")
    downloaded_count = 0

    for page in paginator.paginate(
        Bucket=bucket_name,
        Prefix="raw/",
    ):
        for item in page.get("Contents", []):
            s3_key = item["Key"]

            if s3_key.endswith("/"):
                continue

            relative_key = PurePosixPath(s3_key).relative_to("raw")

            destination = RAW_ROOT.joinpath(
                *relative_key.parts
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            s3_client.download_file(
                bucket_name,
                s3_key,
                str(destination),
            )

            downloaded_count += 1

    print(
        f"Staged {downloaded_count} raw files from S3."
    )

    return downloaded_count


def upload_raw_file(file_path: Path) -> str | None:
    """Upload a raw file to its permanent S3 location."""

    upload_enabled = (
        os.getenv("S3_UPLOAD_ENABLED", "false").lower()
        == "true"
    )

    if not upload_enabled:
        if using_s3_raw_storage():
            raise RuntimeError(
                "RAW_STORAGE_MODE=s3 requires "
                "S3_UPLOAD_ENABLED=true."
            )

        return None

    bucket_name = _get_bucket_name()
    absolute_path, _ = _resolve_raw_file(file_path)
    s3_key = s3_key_for_file(file_path)

    s3_client = _get_s3_client()

    try:
        s3_client.head_object(
            Bucket=bucket_name,
            Key=s3_key,
        )

        print(
            f"S3 object already exists: "
            f"s3://{bucket_name}/{s3_key}"
        )

        return s3_key

    except ClientError as error:
        error_code = error.response.get(
            "Error",
            {},
        ).get("Code", "")

        if error_code not in {
            "404",
            "NoSuchKey",
            "NotFound",
        }:
            raise

    s3_client.upload_file(
        str(absolute_path),
        bucket_name,
        s3_key,
    )

    print(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")

    return s3_key