from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from ontario_energy_warehouse import s3_storage


class FakeS3Client:
    def __init__(self, object_exists: bool):
        self.object_exists = object_exists
        self.uploads = []

    def head_object(self, Bucket, Key):
        if not self.object_exists:
            raise ClientError(
                {
                    "Error": {
                        "Code": "404",
                        "Message": "Not Found",
                    }
                },
                "HeadObject",
            )

        return {}

    def upload_file(self, filename, bucket, key):
        self.uploads.append((filename, bucket, key))


class FakeSession:
    def __init__(self, client):
        self.fake_client = client

    def client(self, service_name):
        assert service_name == "s3"
        return self.fake_client


def create_raw_file(tmp_path: Path, monkeypatch) -> Path:
    project_root = tmp_path
    raw_root = project_root / "data" / "raw"

    file_path = raw_root / "ieso" / "example.csv"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("example data", encoding="utf-8")

    monkeypatch.setattr(
        s3_storage,
        "PROJECT_ROOT",
        project_root,
    )
    monkeypatch.setattr(
        s3_storage,
        "RAW_ROOT",
        raw_root,
    )

    return file_path


def configure_environment(monkeypatch):
    monkeypatch.setenv("S3_UPLOAD_ENABLED", "true")
    monkeypatch.setenv("S3_RAW_BUCKET", "test-bucket")
    monkeypatch.setenv("AWS_PROFILE", "project1")
    monkeypatch.setenv("AWS_REGION", "ca-central-1")


def test_upload_disabled_does_not_contact_aws(monkeypatch):
    monkeypatch.setenv("S3_UPLOAD_ENABLED", "false")

    def fail_session(**kwargs):
        raise AssertionError("AWS should not be contacted")

    monkeypatch.setattr(
        s3_storage.boto3,
        "Session",
        fail_session,
    )

    result = s3_storage.upload_raw_file(
        Path("data/raw/ieso/example.csv")
    )

    assert result is None


def test_missing_bucket_configuration(monkeypatch):
    monkeypatch.setenv("S3_UPLOAD_ENABLED", "true")
    monkeypatch.delenv("S3_RAW_BUCKET", raising=False)

    with pytest.raises(RuntimeError, match="S3_RAW_BUCKET"):
        s3_storage.upload_raw_file(
            Path("data/raw/ieso/example.csv")
        )


def test_new_object_is_uploaded(tmp_path, monkeypatch):
    configure_environment(monkeypatch)
    file_path = create_raw_file(tmp_path, monkeypatch)

    fake_client = FakeS3Client(object_exists=False)

    monkeypatch.setattr(
        s3_storage.boto3,
        "Session",
        lambda **kwargs: FakeSession(fake_client),
    )

    result = s3_storage.upload_raw_file(file_path)

    assert result == "raw/ieso/example.csv"
    assert fake_client.uploads == [
        (
            str(file_path.resolve()),
            "test-bucket",
            "raw/ieso/example.csv",
        )
    ]


def test_existing_object_is_skipped(tmp_path, monkeypatch):
    configure_environment(monkeypatch)
    file_path = create_raw_file(tmp_path, monkeypatch)

    fake_client = FakeS3Client(object_exists=True)

    monkeypatch.setattr(
        s3_storage.boto3,
        "Session",
        lambda **kwargs: FakeSession(fake_client),
    )

    result = s3_storage.upload_raw_file(file_path)

    assert result == "raw/ieso/example.csv"
    assert fake_client.uploads == []