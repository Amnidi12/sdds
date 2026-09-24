"""
Password hashing (Argon2id) and JWT access/refresh token handling.

Design notes:
- Access tokens are short-lived and sent in the Authorization header OR read
  from an HttpOnly cookie by the frontend's server-side proxy.
- Refresh tokens are opaque random strings; only their SHA-256 hash is stored
  in the database (see RefreshSession model), following the same principle
  used for password reset / email verification tokens.
- Argon2id (via argon2-cffi) is used instead of bcrypt/PBKDF2 as it is the
  OWASP-recommended modern default for password hashing.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def generate_opaque_token() -> str:
    """Cryptographically secure random token for refresh/reset/verification tokens."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    """We store only this hash in the DB - never the raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: uuid.UUID, role: str, organization_id: str | None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "org": organization_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.APP_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.APP_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload
