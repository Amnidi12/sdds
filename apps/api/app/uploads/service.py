"""
Secure file upload service.

Security measures (addressing Section 6.2 of the project report):
1. Real MIME verification via Pillow image decoding (not just Content-Type header)
2. File size limit enforced before reading entire file into memory
3. Extension allowlist (png, jpg, jpeg, webp, gif)
4. Randomized storage keys (original filenames never stored as-is)

Storage backends:
- AWS S3 (or any S3-compatible like Supabase Storage) when S3_* env vars are set
- Local disk fallback for development
"""

import io
import logging
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from app.core.config import get_settings

logger = logging.getLogger("app.uploads")
settings = get_settings()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}


def _get_s3_client():
    """Create an S3 client. Works with AWS S3 and Supabase Storage (S3-compatible)."""
    if not settings.S3_ENDPOINT and not settings.S3_BUCKET:
        return None
    kwargs = {
        "service_name": "s3",
        "region_name": settings.S3_REGION,
        "aws_access_key_id": settings.S3_ACCESS_KEY,
        "aws_secret_access_key": settings.S3_SECRET_KEY,
    }
    if settings.S3_ENDPOINT:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT
    return boto3.client(**kwargs)


def validate_file_extension(filename: str | None) -> str:
    """Extract and validate the file extension against the allowlist."""
    if not filename or "." not in filename:
        raise ValueError("File must have a valid extension")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File extension '.{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_image_content(file_bytes: bytes) -> str:
    """Verify the file is a real image by decoding it with Pillow.

    Returns the verified MIME type (e.g. 'image/png').
    This catches files where the Content-Type header was faked.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  # verify it's a real image, raises if corrupt/fake
    except Exception:
        raise ValueError("File content is not a valid image")

    # Re-open after verify (verify() leaves the file in an unusable state)
    img = Image.open(io.BytesIO(file_bytes))
    format_to_mime = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
        "GIF": "image/gif",
    }
    mime = format_to_mime.get(img.format)
    if not mime or mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Image format '{img.format}' is not allowed")
    return mime


async def upload_file(
    file_bytes: bytes,
    original_filename: str | None,
    content_type: str | None,
) -> dict:
    """Upload a file and return storage metadata.

    Returns:
        dict with keys: storage_key, content_type, file_size_bytes
    """
    # 1. Check file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ValueError(f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB")

    if len(file_bytes) == 0:
        raise ValueError("File is empty")

    # 2. Validate extension
    ext = validate_file_extension(original_filename)

    # 3. Validate actual image content (real MIME sniffing via Pillow)
    verified_mime = validate_image_content(file_bytes)

    # 4. Generate a randomized storage key (never use original filename)
    storage_key = f"uploads/{uuid.uuid4().hex}.{ext}"

    # 5. Store the file
    s3_client = _get_s3_client()
    if s3_client and settings.S3_BUCKET:
        try:
            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=storage_key,
                Body=file_bytes,
                ContentType=verified_mime,
            )
            logger.info("Uploaded %s to S3 bucket %s", storage_key, settings.S3_BUCKET)
        except ClientError:
            logger.exception("S3 upload failed for %s", storage_key)
            raise ValueError("File storage service is temporarily unavailable")
    else:
        # Local disk fallback
        local_path = Path(settings.LOCAL_UPLOAD_DIR) / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        logger.info("Saved %s to local disk at %s", storage_key, local_path)

    return {
        "storage_key": storage_key,
        "content_type": verified_mime,
        "file_size_bytes": len(file_bytes),
    }
