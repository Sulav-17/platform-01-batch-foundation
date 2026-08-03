import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"

ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(PROJECT_ROOT / ENV_FILE, override=True)


def upload_raw_file(file_path: Path) -> str | None:
    """Upload a local raw file to S3 without removing the local copy."""

    upload_enabled = (
        os.getenv("S3_UPLOAD_ENABLED", "false").lower() == "true"
    )

    if not upload_enabled:
        return None

    bucket_name = os.getenv("S3_RAW_BUCKET")

    if not bucket_name:
        raise RuntimeError(
            "S3_UPLOAD_ENABLED is true, but S3_RAW_BUCKET is missing."
        )

    aws_profile = os.getenv("AWS_PROFILE")
    aws_region = os.getenv("AWS_REGION")

    absolute_path = Path(file_path)

    if not absolute_path.is_absolute():
        absolute_path = PROJECT_ROOT / absolute_path

    absolute_path = absolute_path.resolve()

    if not absolute_path.exists():
        raise FileNotFoundError(
            f"Raw file does not exist: {absolute_path}"
        )

    try:
        relative_path = absolute_path.relative_to(RAW_ROOT.resolve())
    except ValueError as error:
        raise ValueError(
            f"File must be inside {RAW_ROOT}: {absolute_path}"
        ) from error

    s3_key = f"raw/{relative_path.as_posix()}"

    session_options = {}

    if aws_profile:
        session_options["profile_name"] = aws_profile

    if aws_region:
        session_options["region_name"] = aws_region

    session = boto3.Session(**session_options)
    s3_client = session.client("s3")

    try:
        s3_client.head_object(
            Bucket=bucket_name,
            Key=s3_key,
        )

        print(f"S3 object already exists: s3://{bucket_name}/{s3_key}")
        return s3_key

    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")

        if error_code not in {"404", "NoSuchKey", "NotFound"}:
            raise

    s3_client.upload_file(
        str(absolute_path),
        bucket_name,
        s3_key,
    )

    print(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")

    return s3_key