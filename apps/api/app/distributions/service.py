"""
Distribution business logic.

Notification triggers:
- Notifies the beneficiary when a distribution is created/dispatched/delivered
- Notifies the assigned volunteer when a distribution is created
- Notifies the donor when their donation reaches a beneficiary (transparency loop)
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.beneficiaries.models import Beneficiary
from app.core.deps import CurrentUser
from app.donations.models import Donation, DonationStatus
from app.donations.service import transition_donation_status
from app.notifications.service import create_notification
from app.tasks.models import (
    ALLOWED_DISTRIBUTION_TRANSITIONS,
    DeliveryProof,
    Distribution,
    DistributionItem,
    DistributionStatus,
)
from app.warehouses.models import InventoryBatch
from app.warehouses.service import dispatch_stock, reserve_stock


async def create_distribution(
    db: AsyncSession,
    organization_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    request_id,
    volunteer_id,
    items,
    actor: CurrentUser,
) -> Distribution:
    beneficiary = (
        await db.execute(select(Beneficiary).where(Beneficiary.id == beneficiary_id))
    ).scalar_one_or_none()
    if not beneficiary or beneficiary.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Beneficiary not found in your organization")

    distribution = Distribution(
        organization_id=organization_id,
        beneficiary_id=beneficiary_id,
        request_id=request_id,
        volunteer_id=volunteer_id,
        status=DistributionStatus.CREATED,
    )
    db.add(distribution)
    await db.flush()

    for item in items:
        db.add(
            DistributionItem(
                distribution_id=distribution.id,
                inventory_batch_id=item.inventory_batch_id,
                quantity=item.quantity,
            )
        )

    db.add(
        AuditLog(
            actor_id=actor.id,
            action="distribution.created",
            resource_type="distribution",
            resource_id=str(distribution.id),
        )
    )

    # Notify assigned volunteer about the new distribution
    if volunteer_id:
        await create_notification(
            db,
            user_id=volunteer_id,
            title="New Distribution Assigned",
            body=f"You have been assigned a new distribution for beneficiary '{beneficiary.full_name}'.",
            event_type="distribution.assigned",
            link="/dashboard/volunteer",
        )

    # Notify beneficiary (if they have a user account linked)
    if beneficiary.user_id:
        await create_notification(
            db,
            user_id=beneficiary.user_id,
            title="Distribution Created",
            body="A distribution of donated goods has been prepared for you.",
            event_type="distribution.created",
            link="/dashboard/beneficiary",
        )

    await db.commit()
    await db.refresh(distribution)

    # Reserve stock for every item now that the distribution row exists (needed as `reference`)
    for item in items:
        await reserve_stock(db, item.inventory_batch_id, item.quantity, actor, reference=str(distribution.id))

    await transition_distribution_status(db, distribution, DistributionStatus.RESERVED, actor)
    return distribution


async def transition_distribution_status(
    db: AsyncSession, distribution: Distribution, new_status: DistributionStatus, actor: CurrentUser
) -> Distribution:
    allowed_next = ALLOWED_DISTRIBUTION_TRANSITIONS.get(distribution.status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition distribution from '{distribution.status.value}' to '{new_status.value}'",
        )

    distribution.status = new_status

    if new_status == DistributionStatus.DISPATCHED:
        # Convert reservations into permanent OUT movements
        result = await db.execute(
            select(DistributionItem).where(DistributionItem.distribution_id == distribution.id)
        )
        for item in result.scalars().all():
            await dispatch_stock(
                db, item.inventory_batch_id, item.quantity, actor, reference=str(distribution.id)
            )
        await _advance_source_donations(db, distribution, DonationStatus.OUT_FOR_DISTRIBUTION, actor)

        # Notify beneficiary that goods are on the way
        beneficiary = (
            await db.execute(select(Beneficiary).where(Beneficiary.id == distribution.beneficiary_id))
        ).scalar_one_or_none()
        if beneficiary and beneficiary.user_id:
            await create_notification(
                db,
                user_id=beneficiary.user_id,
                title="Goods Dispatched",
                body="Your donation goods have been dispatched and are on the way!",
                event_type="distribution.dispatched",
                link="/dashboard/beneficiary",
            )

    elif new_status == DistributionStatus.DELIVERED:
        await _advance_source_donations(db, distribution, DonationStatus.DELIVERED, actor)

        # Notify beneficiary of delivery
        beneficiary = (
            await db.execute(select(Beneficiary).where(Beneficiary.id == distribution.beneficiary_id))
        ).scalar_one_or_none()
        if beneficiary and beneficiary.user_id:
            await create_notification(
                db,
                user_id=beneficiary.user_id,
                title="Delivery Complete",
                body="Your donation goods have been delivered.",
                event_type="distribution.delivered",
                link="/dashboard/beneficiary",
            )

    elif new_status == DistributionStatus.COMPLETED:
        # Closes the loop: originating donations are marked COMPLETED so donors see impact (requirement #55)
        await _advance_source_donations(db, distribution, DonationStatus.COMPLETED, actor)

    db.add(
        AuditLog(
            actor_id=actor.id,
            action=f"distribution.status_changed.{new_status.value}",
            resource_type="distribution",
            resource_id=str(distribution.id),
        )
    )
    await db.commit()
    await db.refresh(distribution)
    return distribution


async def _advance_source_donations(
    db: AsyncSession, distribution: Distribution, target_status: DonationStatus, actor: CurrentUser
) -> None:
    """Every donation whose stock fed this distribution gets its lifecycle advanced accordingly."""
    result = await db.execute(
        select(Donation)
        .join(InventoryBatch, InventoryBatch.donation_id == Donation.id)
        .join(DistributionItem, DistributionItem.inventory_batch_id == InventoryBatch.id)
        .where(DistributionItem.distribution_id == distribution.id)
    )
    donations = {d.id: d for d in result.scalars().all()}
    for donation in donations.values():
        if donation.status != target_status:
            try:
                await transition_donation_status(
                    db, donation, target_status, actor, note="Advanced via linked distribution"
                )
            except HTTPException:
                # Donation may already be ahead in its lifecycle (e.g. shared across multiple
                # distributions) - skip rather than fail the whole distribution transition.
                pass


async def submit_delivery_proof(
    db: AsyncSession,
    distribution: Distribution,
    recipient_confirmation_name: str | None,
    note: str | None,
    photo_storage_key: str | None,
    actor: CurrentUser,
) -> DeliveryProof:
    proof = DeliveryProof(
        distribution_id=distribution.id,
        recipient_confirmation_name=recipient_confirmation_name,
        note=note,
        photo_storage_key=photo_storage_key,
    )
    db.add(proof)
    db.add(
        AuditLog(
            actor_id=actor.id,
            action="distribution.proof_submitted",
            resource_type="distribution",
            resource_id=str(distribution.id),
        )
    )
    await db.commit()
    await db.refresh(proof)
    return proof


async def get_distribution_or_404(db: AsyncSession, distribution_id: uuid.UUID) -> Distribution:
    result = await db.execute(select(Distribution).where(Distribution.id == distribution_id))
    distribution = result.scalar_one_or_none()
    if not distribution:
        raise HTTPException(status_code=404, detail="Distribution not found")
    return distribution
