"""
Pickup task business logic.

Notification triggers:
- Notifies the volunteer when assigned a pickup task
- Notifies the donor when pickup status progresses
- Notifies NGO admin when pickup is completed
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.core.deps import CurrentUser
from app.donations.models import DonationStatus
from app.donations.service import get_donation_or_404, transition_donation_status
from app.notifications.service import create_notification
from app.tasks.models import ALLOWED_PICKUP_TRANSITIONS, PickupTask, PickupTaskStatus
from app.users.models import RoleName


async def create_pickup_task(
    db: AsyncSession, donation_id: uuid.UUID, volunteer_id: uuid.UUID | None, scheduled_at, actor: CurrentUser
) -> PickupTask:
    donation = await get_donation_or_404(db, donation_id)
    if donation.status != DonationStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Donation must be approved before scheduling pickup")

    task = PickupTask(donation_id=donation_id, volunteer_id=volunteer_id, scheduled_at=scheduled_at)
    db.add(task)
    await db.flush()

    await transition_donation_status(
        db, donation, DonationStatus.PICKUP_SCHEDULED, actor, note="Pickup task created"
    )
    db.add(
        AuditLog(
            actor_id=actor.id,
            action="pickup_task.created",
            resource_type="pickup_task",
            resource_id=str(task.id),
        )
    )

    # Notify the assigned volunteer
    if volunteer_id:
        await create_notification(
            db,
            user_id=volunteer_id,
            title="New Pickup Task Assigned",
            body=f"You have been assigned to pick up donation '{donation.title}' (Tracking: {donation.tracking_id}).",
            event_type="pickup.assigned",
            link=f"/dashboard/volunteer",
        )

    await db.commit()
    await db.refresh(task)
    return task


async def update_pickup_task_status(
    db: AsyncSession,
    task: PickupTask,
    new_status: PickupTaskStatus,
    actor: CurrentUser,
    note: str | None = None,
) -> PickupTask:
    allowed_next = ALLOWED_PICKUP_TRANSITIONS.get(task.status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition pickup task from '{task.status.value}' to '{new_status.value}'",
        )

    # Volunteers may only update their own assigned tasks
    if actor.role == RoleName.VOLUNTEER and task.volunteer_id != actor.id:
        raise HTTPException(status_code=403, detail="This task is not assigned to you")

    task.status = new_status
    if note:
        task.note = note

    # Keep the donation's overall lifecycle in sync with pickup progress
    donation = await get_donation_or_404(db, task.donation_id)
    if new_status == PickupTaskStatus.PICKED_UP:
        await transition_donation_status(
            db, donation, DonationStatus.PICKED_UP, actor, note="Picked up by volunteer"
        )
    elif new_status == PickupTaskStatus.COMPLETED:
        await transition_donation_status(
            db,
            donation,
            DonationStatus.RECEIVED_AT_WAREHOUSE,
            actor,
            note="Pickup completed, received at warehouse",
        )

    db.add(
        AuditLog(
            actor_id=actor.id,
            action=f"pickup_task.status_changed.{new_status.value}",
            resource_type="pickup_task",
            resource_id=str(task.id),
        )
    )

    # Notify the donor about pickup progress
    _pickup_donor_messages = {
        PickupTaskStatus.EN_ROUTE: ("Volunteer En Route", "A volunteer is on the way to pick up your donation."),
        PickupTaskStatus.ARRIVED: ("Volunteer Arrived", "The volunteer has arrived at the pickup location."),
        PickupTaskStatus.FAILED: ("Pickup Failed", "The pickup attempt was unsuccessful. The NGO will reschedule."),
    }
    if new_status in _pickup_donor_messages:
        title, body = _pickup_donor_messages[new_status]
        await create_notification(
            db,
            user_id=donation.donor_id,
            title=title,
            body=f"{body} (Tracking: {donation.tracking_id})",
            event_type=f"pickup.{new_status.value}",
            link=f"/dashboard/donations/{donation.id}",
        )

    await db.commit()
    await db.refresh(task)
    return task


async def get_pickup_task_or_404(db: AsyncSession, task_id: uuid.UUID) -> PickupTask:
    result = await db.execute(select(PickupTask).where(PickupTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Pickup task not found")
    return task
