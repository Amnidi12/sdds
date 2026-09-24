"""
Reusable FastAPI dependencies for authentication and role-based authorization.

Every protected route MUST depend on `get_current_user` (or a role-restricted
wrapper below). The frontend hiding a button is never sufficient - these
dependencies are the actual enforcement point.
"""

import uuid

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.users.models import RoleName, User


class CurrentUser:
    def __init__(self, id: uuid.UUID, role: RoleName, organization_id: uuid.UUID | None, email: str):
        self.id = id
        self.role = role
        self.organization_id = organization_id
        self.email = email


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(access_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return CurrentUser(id=user.id, role=user.role, organization_id=user.organization_id, email=user.email)


def require_roles(*allowed_roles: RoleName):
    """Dependency factory: raises 403 unless the current user has one of the allowed roles."""

    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _checker


async def require_same_organization(organization_id: uuid.UUID, current_user: CurrentUser) -> None:
    """Ensures an NGO admin/volunteer can only act within their own organization."""
    if current_user.role == RoleName.SUPER_ADMIN:
        return
    if current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Resource belongs to a different organization"
        )
