import asyncio
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


@dataclass(frozen=True)
class StoredImage:
    media_type: str
    content: bytes | None = None
    path: Path | None = None


class ImageStorage(Protocol):
    async def save(self, image_path: str) -> str:
        """Persist an image and return its API-compatible ID."""

    async def get(self, image_id: str) -> StoredImage | None:
        """Return an image by ID, or None when it does not exist."""


def _safe_filename(image_id: str) -> str | None:
    normalized = image_id.replace("\\", "/")
    if not normalized or "/" in normalized or normalized in {".", ".."}:
        return None
    return normalized


def _media_type(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


class LocalImageStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    async def save(self, image_path: str) -> str:
        filename = Path(image_path).name
        return f"data/{filename}"

    async def get(self, image_id: str) -> StoredImage | None:
        filename = _safe_filename(image_id)
        if filename is None:
            return None

        path = self.data_dir / filename
        if not path.is_file():
            return None

        return StoredImage(path=path, media_type=_media_type(filename))


class S3ImageStorage:
    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str = "auto",
        prefix: str = "",
        client=None,
    ):
        if not bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        if not endpoint_url:
            raise ValueError("S3_ENDPOINT_URL is required when STORAGE_BACKEND=s3")
        if not access_key_id:
            raise ValueError("AWS_ACCESS_KEY_ID is required when STORAGE_BACKEND=s3")
        if not secret_access_key:
            raise ValueError(
                "AWS_SECRET_ACCESS_KEY is required when STORAGE_BACKEND=s3"
            )

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = client or boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def _object_key(self, filename: str) -> str:
        if self.prefix:
            return f"{self.prefix}/{filename}"
        return filename

    async def save(self, image_path: str) -> str:
        path = Path(image_path)
        filename = path.name
        key = self._object_key(filename)

        await asyncio.to_thread(
            self.client.upload_file,
            str(path),
            self.bucket,
            key,
            ExtraArgs={"ContentType": _media_type(filename)},
        )
        await asyncio.to_thread(path.unlink, missing_ok=True)
        return f"data/{filename}"

    async def get(self, image_id: str) -> StoredImage | None:
        filename = _safe_filename(image_id)
        if filename is None:
            return None

        try:
            response = await asyncio.to_thread(
                self.client.get_object,
                Bucket=self.bucket,
                Key=self._object_key(filename),
            )
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

        body = response["Body"]
        try:
            content = await asyncio.to_thread(body.read)
        finally:
            body.close()

        return StoredImage(
            media_type=response.get("ContentType") or _media_type(filename),
            content=content,
        )


def create_image_storage() -> ImageStorage:
    backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    if backend == "local":
        return LocalImageStorage()
    if backend in {"s3", "r2"}:
        return S3ImageStorage(
            bucket=os.getenv("S3_BUCKET", ""),
            endpoint_url=os.getenv("S3_ENDPOINT_URL", ""),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region=os.getenv("AWS_DEFAULT_REGION", "auto"),
            prefix=os.getenv("S3_PREFIX", ""),
        )
    raise ValueError(
        f"Unsupported STORAGE_BACKEND: {backend}. Expected 'local' or 's3'."
    )
