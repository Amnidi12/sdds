"""
File upload endpoint.

Security:
- Rate-limited specifically (large-file abuse vector)
- Uses CurrentUser type hint (not the ORM User model) — Section 6.4 fix
- Delegates all validation to uploads/service.py (MIME sniffing, size, extension)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.core.rate_limit import is_rate_limited
from app.db.session import get_db
from app.uploads.service import upload_file

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])
settings = get_settings()


@router.post("")
async def upload_image(
    file: UploadFile,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image file. Returns a storage key for later reference.

    - Max file size: configured via MAX_UPLOAD_SIZE_MB (default 10 MB)
    - Allowed formats: PNG, JPEG, WebP, GIF
    - Content is verified via Pillow (not just the Content-Type header)
    """
    # Rate-limit uploads specifically (separate from global rate limit)
    if is_rate_limited(f"upload:{current_user.id}", max_requests=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Upload rate limit exceeded. Try again shortly.")

    # Check size hint before reading (UploadFile.size is set by the ASGI server)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Read file contents
    contents = await file.read()

    try:
        result = await upload_file(contents, file.filename, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "storage_key": result["storage_key"],
        "content_type": result["content_type"],
        "file_size_bytes": result["file_size_bytes"],
    }
