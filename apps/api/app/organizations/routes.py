import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.users.models import RoleName, User
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])

def _generate_slug(name: str) -> str:
    # basic slugification
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Register a new NGO organization. The user will be linked to it."""
    if current_user.organization_id:
        raise HTTPException(status_code=400, detail="User is already part of an organization")

    # Generate slug and ensure uniqueness
    base_slug = _generate_slug(payload.name)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(Organization).where(Organization.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        name=payload.name,
        slug=slug,
        description=payload.description,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        address=payload.address,
        is_verified=False
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # Link the user to the new org
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    user.organization_id = org.id
    await db.commit()
    
    return org

class OrgMemberOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: RoleName

    model_config = {"from_attributes": True}


@router.get("/members", response_model=list[OrgMemberOut])
async def list_organization_members(
    role: RoleName | None = None,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Used by NGO staff to see e.g. their volunteers when assigning pickup/distribution tasks."""
    query = select(User).where(User.organization_id == current_user.organization_id, User.is_active.is_(True))
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query)
    return result.scalars().all()
