"""
Admin-specific Pydantic schemas.
Previously these were inline in admin/routes.py — extracted here for clarity.
"""

import uuid

from pydantic import BaseModel

from app.users.models import RoleName


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    contact_email: str | None
    is_verified: bool
    is_active: bool

    model_config = {"from_attributes": True}


class UserAdminOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: RoleName
    organization_id: uuid.UUID | None
    is_active: bool
    is_email_verified: bool

    model_config = {"from_attributes": True}


class RoleChangeRequest(BaseModel):
    new_role: RoleName


class StatusChangeRequest(BaseModel):
    is_active: bool
