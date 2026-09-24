"""
Super Admin endpoints.

Provides platform-wide statistics, organization management (list, verify),
and user management (list, change role, change status).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    OrganizationOut,
    RoleChangeRequest,
    StatusChangeRequest,
    UserAdminOut,
)
from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.donations.models import Donation, DonationStatus
from app.organizations.models import Organization
from app.tasks.models import Distribution, DistributionStatus
from app.users.models import RoleName, User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ---- Stats ----


@router.get("/stats")
async def platform_stats(
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide metrics for the Super Admin dashboard. Real counts, not vanity numbers."""
    org_count = (await db.execute(select(func.count()).select_from(Organization))).scalar_one()
    user_count = (
        await db.execute(select(func.count()).select_from(User).where(User.is_active.is_(True)))
    ).scalar_one()
    donation_count = (await db.execute(select(func.count()).select_from(Donation))).scalar_one()
    pending_review_count = (
        await db.execute(
            select(func.count()).select_from(Donation).where(Donation.status == DonationStatus.PENDING_REVIEW)
        )
    ).scalar_one()
    completed_donation_count = (
        await db.execute(
            select(func.count()).select_from(Donation).where(Donation.status == DonationStatus.COMPLETED)
        )
    ).scalar_one()
    completed_distribution_count = (
        await db.execute(
            select(func.count()).select_from(Distribution).where(
                Distribution.status == DistributionStatus.COMPLETED
            )
        )
    ).scalar_one()

    return {
        "organizations": org_count,
        "active_users": user_count,
        "total_donations": donation_count,
        "pending_review": pending_review_count,
        "completed_donations": completed_donation_count,
        "completed_distributions": completed_distribution_count,
    }


# ---- Organization management ----


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    verified_only: bool = False,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations on the platform."""
    query = select(Organization)
    if verified_only:
        query = query.where(Organization.is_verified.is_(True))
    query = query.order_by(Organization.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/organizations/{organization_id}/verify", response_model=OrganizationOut)
async def verify_organization(
    organization_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Verify an organization, allowing it to receive and manage donations."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.is_verified = True
    await db.commit()
    await db.refresh(org)
    return org


# ---- User management ----


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(
    role: RoleName | None = None,
    active_only: bool = True,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users on the platform with optional filters."""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if active_only:
        query = query.where(User.is_active.is_(True))
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/users/{user_id}/role", response_model=UserAdminOut)
async def change_user_role(
    user_id: uuid.UUID,
    payload: RoleChangeRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role. Only super admins can do this."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.new_role
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/status", response_model=UserAdminOut)
async def change_user_status(
    user_id: uuid.UUID,
    payload: StatusChangeRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a user account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = payload.is_active
    await db.commit()
    await db.refresh(user)
    return user
