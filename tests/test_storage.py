import asyncio
import io
from pathlib import Path

from botocore.exceptions import ClientError

from src.storage import LocalImageStorage, S3ImageStorage


class FakeS3Client:
    def __init__(self):
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    def upload_file(self, filename, bucket, key, ExtraArgs):
        self.objects[(bucket, key)] = (
            Path(filename).read_bytes(),
            ExtraArgs["ContentType"],
        )

    def get_object(self, *, Bucket, Key):
        try:
            content, content_type = self.objects[(Bucket, Key)]
        except KeyError as exc:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
                "GetObject",
            ) from exc
        return {"Body": io.BytesIO(content), "ContentType": content_type}


def test_local_storage_preserves_api_id(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    image_path = data_dir / "rendered_test.jpeg"
    image_path.write_bytes(b"jpeg")
    storage = LocalImageStorage(str(data_dir))

    image_id = asyncio.run(storage.save(str(image_path)))
    stored = asyncio.run(storage.get("rendered_test.jpeg"))

    assert image_id == "data/rendered_test.jpeg"
    assert stored is not None
    assert stored.path == image_path
    assert stored.media_type == "image/jpeg"


def test_local_storage_rejects_unsafe_id(tmp_path):
    storage = LocalImageStorage(str(tmp_path))

    assert asyncio.run(storage.get("../secret")) is None
    assert asyncio.run(storage.get("nested/image.jpeg")) is None


def test_s3_storage_round_trip_and_removes_local_file(tmp_path):
    image_path = tmp_path / "rendered_test.jpeg"
    image_path.write_bytes(b"jpeg")
    client = FakeS3Client()
    storage = S3ImageStorage(
        bucket="test-bucket",
        endpoint_url="https://example.invalid",
        access_key_id="access-key",
        secret_access_key="secret-key",
        prefix="images",
        client=client,
    )

    image_id = asyncio.run(storage.save(str(image_path)))
    stored = asyncio.run(storage.get("rendered_test.jpeg"))

    assert image_id == "data/rendered_test.jpeg"
    assert not image_path.exists()
    assert stored is not None
    assert stored.content == b"jpeg"
    assert stored.media_type == "image/jpeg"
    assert ("test-bucket", "images/rendered_test.jpeg") in client.objects


def test_s3_storage_returns_none_for_missing_object():
    storage = S3ImageStorage(
        bucket="test-bucket",
        endpoint_url="https://example.invalid",
        access_key_id="access-key",
        secret_access_key="secret-key",
        client=FakeS3Client(),
    )

    assert asyncio.run(storage.get("missing.jpeg")) is None
