"""Storage abstraction -- local filesystem or S3-compatible (R2, MinIO, AWS S3).

Usage:
    from app.storage import upload_file, download_file, file_exists, delete_file

All public functions are async-safe.  The S3 backend wraps boto3 (synchronous)
via ``asyncio.to_thread`` so the event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger("arcadeforge.storage")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def upload_file(
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload *data* under *key*.  Returns the storage key."""
    if settings.storage_driver == "s3":
        return await _s3_upload(key, data, content_type)
    return await asyncio.to_thread(_local_upload, key, data)


async def download_file(key: str) -> bytes:
    """Download the object identified by *key*."""
    if settings.storage_driver == "s3":
        return await _s3_download(key)
    return await asyncio.to_thread(_local_download, key)


async def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Return a presigned download URL (S3) or a local file path (local)."""
    if settings.storage_driver == "s3":
        return await _s3_presigned_url(key, expires_in)
    return _local_path(key)


async def file_exists(key: str) -> bool:
    """Check whether *key* exists in storage."""
    if settings.storage_driver == "s3":
        return await _s3_exists(key)
    return _local_exists(key)


async def delete_file(key: str) -> None:
    """Delete the object at *key*.  No error if it does not exist."""
    if settings.storage_driver == "s3":
        await _s3_delete(key)
    else:
        await asyncio.to_thread(_local_delete, key)


async def list_files(prefix: str) -> list[str]:
    """List all keys that start with *prefix*."""
    if settings.storage_driver == "s3":
        return await _s3_list(prefix)
    return await asyncio.to_thread(_local_list, prefix)


# ---------------------------------------------------------------------------
# Local filesystem backend
# ---------------------------------------------------------------------------

def _local_root() -> Path:
    return Path(settings.storage_local_path).resolve()


def _local_full(key: str) -> Path:
    """Resolve *key* to an absolute path under the local root.

    Prevents path traversal by ensuring the resolved path stays inside the
    storage root.
    """
    full = (_local_root() / key).resolve()
    if not str(full).startswith(str(_local_root())):
        raise ValueError(f"Invalid storage key (path traversal): {key}")
    return full


def _local_upload(key: str, data: bytes) -> str:
    dest = _local_full(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    logger.debug("local upload: %s (%d bytes)", key, len(data))
    return key


def _local_download(key: str) -> bytes:
    src = _local_full(key)
    if not src.is_file():
        raise FileNotFoundError(f"Storage key not found: {key}")
    return src.read_bytes()


def _local_path(key: str) -> str:
    return str(_local_full(key))


def _local_exists(key: str) -> bool:
    return _local_full(key).is_file()


def _local_delete(key: str) -> None:
    target = _local_full(key)
    if target.is_file():
        target.unlink()
        logger.debug("local delete: %s", key)


def _local_list(prefix: str) -> list[str]:
    root = _local_root()
    base = (root / prefix).resolve()
    if not str(base).startswith(str(root)):
        raise ValueError(f"Invalid prefix (path traversal): {prefix}")
    if not base.exists():
        return []
    # If prefix points to a directory, list recursively
    if base.is_dir():
        search_dir = base
    else:
        search_dir = base.parent
    results: list[str] = []
    for path in search_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(root)).replace("\\", "/")
            if rel.startswith(prefix):
                results.append(rel)
    return sorted(results)


# ---------------------------------------------------------------------------
# S3 backend (boto3, wrapped with asyncio.to_thread)
# ---------------------------------------------------------------------------

_s3_client: "S3Client | None" = None


def _get_s3_client() -> "S3Client":
    """Lazily create and cache a boto3 S3 client.

    The client is thread-safe for read operations.  boto3 is imported here
    so it is only required when ``storage_driver == "s3"``.
    """
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required for S3 storage. "
            "Install it with: pip install 'arcadeforge-api[s3]'"
        ) from exc

    kwargs: dict = {
        "region_name": settings.s3_region,
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_access_key_id:
        kwargs["aws_access_key_id"] = settings.s3_access_key_id
        kwargs["aws_secret_access_key"] = settings.s3_secret_access_key

    _s3_client = boto3.client("s3", **kwargs)
    logger.info(
        "S3 client initialised (bucket=%s, endpoint=%s)",
        settings.s3_bucket,
        settings.s3_endpoint_url or "default",
    )
    return _s3_client


def _s3_upload_sync(key: str, data: bytes, content_type: str) -> str:
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    logger.debug("s3 upload: %s (%d bytes)", key, len(data))
    return key


def _s3_download_sync(key: str) -> bytes:
    client = _get_s3_client()
    resp = client.get_object(Bucket=settings.s3_bucket, Key=key)
    return resp["Body"].read()


def _s3_presigned_url_sync(key: str, expires_in: int) -> str:
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def _s3_exists_sync(key: str) -> bool:
    client = _get_s3_client()
    try:
        client.head_object(Bucket=settings.s3_bucket, Key=key)
        return True
    except Exception as exc:
        # head_object raises ClientError with a 404 HTTP status code
        response = getattr(exc, "response", None)
        if response is not None:
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status == 404:
                return False
        raise


def _s3_delete_sync(key: str) -> None:
    client = _get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)
    logger.debug("s3 delete: %s", key)


def _s3_list_sync(prefix: str) -> list[str]:
    client = _get_s3_client()
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


# Async wrappers that delegate to the sync functions via to_thread

async def _s3_upload(key: str, data: bytes, content_type: str) -> str:
    return await asyncio.to_thread(_s3_upload_sync, key, data, content_type)


async def _s3_download(key: str) -> bytes:
    return await asyncio.to_thread(_s3_download_sync, key)


async def _s3_presigned_url(key: str, expires_in: int) -> str:
    return await asyncio.to_thread(_s3_presigned_url_sync, key, expires_in)


async def _s3_exists(key: str) -> bool:
    return await asyncio.to_thread(_s3_exists_sync, key)


async def _s3_delete(key: str) -> None:
    await asyncio.to_thread(_s3_delete_sync, key)


async def _s3_list(prefix: str) -> list[str]:
    return await asyncio.to_thread(_s3_list_sync, prefix)
