import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.donations.models import Donation, DonationCategory, DonationStatus
from app.donations.schemas import (
    DonationCreate,
    DonationDetailOut,
    DonationOut,
    DonationStatusUpdate,
    PublicTrackingOut,
)
from app.donations.service import (
    assert_can_view_donation,
    create_donation,
    get_donation_or_404,
    transition_donation_status,
)
from app.users.models import RoleName

router = APIRouter(prefix="/api/v1/donations", tags=["donations"])


@router.post("", response_model=DonationOut, status_code=201)
async def create_new_donation(
    payload: DonationCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.DONOR)),
    db: AsyncSession = Depends(get_db),
):
    return await create_donation(db, current_user, payload)


@router.get("", response_model=list[DonationOut])
async def list_donations(
    status_filter: DonationStatus | None = Query(default=None, alias="status"),
    category_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Server-side paginated + filtered listing, scoped by role (requirement #19, #8)."""
    query = select(Donation)

    if current_user.role == RoleName.DONOR:
        query = query.where(Donation.donor_id == current_user.id)
    elif current_user.role in (RoleName.NGO_ADMIN, RoleName.VOLUNTEER):
        query = query.where(Donation.organization_id == current_user.organization_id)
    # SUPER_ADMIN sees everything

    if status_filter:
        query = query.where(Donation.status == status_filter)
    if category_id:
        query = query.where(Donation.category_id == category_id)

    query = query.order_by(Donation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{donation_id}", response_model=DonationDetailOut)
async def get_donation(
    donation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    donation = await get_donation_or_404(db, donation_id, with_history=True)
    assert_can_view_donation(donation, current_user)
    return donation


@router.patch("/{donation_id}/status", response_model=DonationOut)
async def update_donation_status(
    donation_id: uuid.UUID,
    payload: DonationStatusUpdate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    donation = await get_donation_or_404(db, donation_id)
    if current_user.role == RoleName.NGO_ADMIN and donation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")

    return await transition_donation_status(
        db,
        donation,
        payload.new_status,
        current_user,
        note=payload.note,
        rejection_reason=payload.rejection_reason,
    )


@router.get("/track/{tracking_id}", response_model=PublicTrackingOut)
async def public_track_donation(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint (no auth) - deliberately returns only a limited status
    view, never donor/beneficiary PII (requirement #10).
    """
    result = await db.execute(
        select(Donation, DonationCategory.name)
        .join(DonationCategory, Donation.category_id == DonationCategory.id)
        .where(Donation.tracking_id == tracking_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
    donation, category_name = row
    return PublicTrackingOut(
        tracking_id=donation.tracking_id,
        category_name=category_name,
        status=donation.status,
        created_at=donation.created_at,
    )
