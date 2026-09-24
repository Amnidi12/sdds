"""
Business logic for donations, kept out of route handlers per clean-architecture
requirement #36. This is the single place status transitions are validated,
so no code path can force an invalid/arbitrary status jump (requirement #11).

Notification triggers (Phase 4):
- Fires notifications to relevant users on key status transitions.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.models import AuditLog
from app.core.deps import CurrentUser
from app.donations.models import (
    ALLOWED_DONATION_TRANSITIONS,
    Donation,
    DonationStatus,
    DonationStatusHistory,
)
from app.donations.schemas import DonationCreate
from app.donations.tracking import generate_tracking_id
from app.notifications.service import create_notification
from app.organizations.models import Organization
from app.users.models import RoleName


# Maps donation status transitions to notification messages for the donor
_DONOR_NOTIFICATION_MAP: dict[DonationStatus, tuple[str, str]] = {
    DonationStatus.APPROVED: (
        "Donation Approved",
        "Your donation has been approved and is ready for pickup scheduling.",
    ),
    DonationStatus.REJECTED: (
        "Donation Not Accepted",
        "Unfortunately, your donation could not be accepted at this time.",
    ),
    DonationStatus.PICKUP_SCHEDULED: (
        "Pickup Scheduled",
        "A volunteer has been assigned to pick up your donation.",
    ),
    DonationStatus.PICKED_UP: (
        "Donation Picked Up",
        "Your donation has been picked up by a volunteer.",
    ),
    DonationStatus.RECEIVED_AT_WAREHOUSE: (
        "Received at Warehouse",
        "Your donation has been received at the warehouse.",
    ),
    DonationStatus.DELIVERED: (
        "Donation Delivered",
        "Your donation has been delivered to a beneficiary!",
    ),
    DonationStatus.COMPLETED: (
        "Donation Journey Complete",
        "Your donation has completed its journey and made an impact. Thank you!",
    ),
}


async def create_donation(db: AsyncSession, donor: CurrentUser, payload: DonationCreate) -> Donation:
    # Ensure tracking ID uniqueness (astronomically unlikely to collide, but be defensive)
    for _ in range(5):
        candidate = generate_tracking_id()
        existing = await db.execute(select(Donation).where(Donation.tracking_id == candidate))
        if not existing.scalar_one_or_none():
            tracking_id = candidate
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate a unique tracking ID, please retry")

    # Auto-assign to the first available organization.
    # In a full multi-NGO system, donors would select the NGO or it would be geo-routed.
    org_result = await db.execute(select(Organization).limit(1))
    organization = org_result.scalar_one_or_none()
    org_id = organization.id if organization else None

    donation = Donation(
        tracking_id=tracking_id,
        donor_id=donor.id,
        organization_id=org_id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        quantity=payload.quantity,
        unit=payload.unit,
        estimated_weight_kg=payload.estimated_weight_kg,
        condition=payload.condition,
        pickup_required=payload.pickup_required,
        pickup_address=payload.pickup_address,
        preferred_pickup_at=payload.preferred_pickup_at,
        expiry_date=payload.expiry_date,
        notes=payload.notes,
        status=DonationStatus.PENDING_REVIEW,
    )
    db.add(donation)
    await db.flush()

    db.add(
        DonationStatusHistory(
            donation_id=donation.id,
            from_status=None,
            to_status=DonationStatus.PENDING_REVIEW,
            actor_id=donor.id,
        )
    )
    db.add(
        AuditLog(
            actor_id=donor.id,
            action="donation.created",
            resource_type="donation",
            resource_id=str(donation.id),
        )
    )
    await db.commit()
    await db.refresh(donation)
    return donation


async def transition_donation_status(
    db: AsyncSession,
    donation: Donation,
    new_status: DonationStatus,
    actor: CurrentUser,
    note: str | None = None,
    rejection_reason: str | None = None,
) -> Donation:
    # Only NGO admins / super admins / volunteers (for pickup-adjacent states) can transition.
    # Fine-grained per-status role checks are enforced in the route layer via require_roles;
    # here we enforce the state machine itself.
    allowed_next = ALLOWED_DONATION_TRANSITIONS.get(donation.status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition donation from '{donation.status.value}' to '{new_status.value}'",
        )

    old_status = donation.status
    donation.status = new_status
    if new_status == DonationStatus.REJECTED:
        donation.rejection_reason = rejection_reason

    db.add(
        DonationStatusHistory(
            donation_id=donation.id,
            from_status=old_status,
            to_status=new_status,
            actor_id=actor.id,
            note=note,
        )
    )
    db.add(
        AuditLog(
            actor_id=actor.id,
            action=f"donation.status_changed.{new_status.value}",
            resource_type="donation",
            resource_id=str(donation.id),
            metadata_json={"from": old_status.value, "to": new_status.value},
        )
    )

    # Fire notification to the donor on key transitions
    if new_status in _DONOR_NOTIFICATION_MAP:
        title, body = _DONOR_NOTIFICATION_MAP[new_status]
        if rejection_reason and new_status == DonationStatus.REJECTED:
            body = f"{body} Reason: {rejection_reason}"
        await create_notification(
            db,
            user_id=donation.donor_id,
            title=title,
            body=f"{body} (Tracking: {donation.tracking_id})",
            event_type=f"donation.{new_status.value}",
            link=f"/dashboard/donations/{donation.id}",
        )

    await db.commit()
    await db.refresh(donation)
    return donation


async def get_donation_or_404(
    db: AsyncSession, donation_id: uuid.UUID, with_history: bool = False
) -> Donation:
    query = select(Donation).where(Donation.id == donation_id)
    if with_history:
        # Eager-load to avoid async lazy-loading (MissingGreenlet) errors when the
        # response is serialized after the request-scoped session may have moved on.
        query = query.options(selectinload(Donation.status_history))
    result = await db.execute(query)
    donation = result.scalar_one_or_none()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


def assert_can_view_donation(donation: Donation, user: CurrentUser) -> None:
    if user.role == RoleName.SUPER_ADMIN:
        return
    if user.role == RoleName.DONOR and donation.donor_id == user.id:
        return
    if (
        user.role in (RoleName.NGO_ADMIN, RoleName.VOLUNTEER)
        and donation.organization_id == user.organization_id
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this donation"
    )
