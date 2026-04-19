from __future__ import annotations

from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from src.common.config import config


def get_boto3_session():
    """
    Create a boto3 session using the configured AWS region.

    Authentication is expected to come from the environment, instance role,
    AWS profile, or other standard boto3 credential sources.
    """
    return boto3.Session(region_name=config.aws["region"])


def get_s3_client():
    """Return an S3 client bound to the configured AWS region."""
    return get_boto3_session().client("s3")


def get_s3_resource():
    """Return an S3 resource bound to the configured AWS region."""
    return get_boto3_session().resource("s3")


def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    """
    Parse an S3 URI into (bucket, key).

    Examples
    --------
    s3://my-bucket/path/to/file.parquet -> ("my-bucket", "path/to/file.parquet")
    s3://my-bucket -> ("my-bucket", "")
    """
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    remainder = s3_uri[len("s3://") :]
    parts = remainder.split("/", 1)

    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""

    if not bucket:
        raise ValueError(f"Missing bucket in S3 URI: {s3_uri}")

    return bucket, key


def build_s3_uri(bucket: str, key: str = "") -> str:
    """
    Build an S3 URI from bucket and key.

    Examples
    --------
    build_s3_uri("my-bucket", "a/b") -> "s3://my-bucket/a/b"
    build_s3_uri("my-bucket", "") -> "s3://my-bucket"
    """
    if not bucket:
        raise ValueError("Bucket name cannot be empty")

    key = key.lstrip("/")
    return f"s3://{bucket}" if not key else f"s3://{bucket}/{key}"


def s3_object_exists(s3_uri: str) -> bool:
    """
    Return True if the exact S3 object exists, else False.

    This checks a single object key, not whether a prefix contains objects.
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not key:
        return False

    client = get_s3_client()

    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def s3_prefix_exists(s3_uri: str) -> bool:
    """
    Return True if at least one object exists under the given S3 prefix.

    Works for both:
    - s3://bucket/prefix
    - s3://bucket/prefix/
    """
    bucket, prefix = parse_s3_uri(s3_uri)
    client = get_s3_client()

    response = client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        MaxKeys=1,
    )
    return response.get("KeyCount", 0) > 0


def list_s3_objects(s3_uri: str, max_keys: int = 1000) -> list[str]:
    """
    List object URIs under an S3 prefix.

    Returns fully qualified S3 URIs.
    """
    bucket, prefix = parse_s3_uri(s3_uri)
    client = get_s3_client()

    response = client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        MaxKeys=max_keys,
    )

    contents = response.get("Contents", [])
    return [build_s3_uri(bucket, obj["Key"]) for obj in contents]


def upload_file_to_s3(local_path: str | Path, s3_uri: str) -> None:
    """
    Upload a local file to an S3 object URI.
    """
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    bucket, key = parse_s3_uri(s3_uri)
    if not key:
        raise ValueError(f"S3 URI must include an object key for upload: {s3_uri}")

    client = get_s3_client()
    client.upload_file(str(local_path), bucket, key)


def download_file_from_s3(s3_uri: str, local_path: str | Path) -> None:
    """
    Download an S3 object URI to a local file path.
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not key:
        raise ValueError(f"S3 URI must include an object key for download: {s3_uri}")

    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    client = get_s3_client()
    client.download_file(bucket, key, str(local_path))


def get_bucket_name(s3_uri: str) -> str:
    """Convenience helper to return only the bucket from an S3 URI."""
    bucket, _ = parse_s3_uri(s3_uri)
    return bucket


def get_object_key(s3_uri: str) -> str:
    """Convenience helper to return only the key from an S3 URI."""
    _, key = parse_s3_uri(s3_uri)
    return key


def join_s3_key(*parts: Optional[str]) -> str:
    """
    Join S3 key fragments safely without duplicate slashes.

    Examples
    --------
    join_s3_key("bronze", "isd", "year=2025") -> "bronze/isd/year=2025"
    """
    cleaned = [part.strip("/") for part in parts if part]
    return "/".join(cleaned)