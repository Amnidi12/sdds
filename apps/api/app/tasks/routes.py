import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.donations.service import get_donation_or_404
from app.tasks.models import PickupTask
from app.tasks.schemas import PickupTaskCreate, PickupTaskOut, PickupTaskStatusUpdate
from app.tasks.service import create_pickup_task, get_pickup_task_or_404, update_pickup_task_status
from app.users.models import RoleName

router = APIRouter(prefix="/api/v1/pickups", tags=["pickups"])


@router.post("", response_model=PickupTaskOut, status_code=201)
async def schedule_pickup(
    payload: PickupTaskCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    donation = await get_donation_or_404(db, payload.donation_id)
    if current_user.role == RoleName.NGO_ADMIN and donation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")
    return await create_pickup_task(
        db, payload.donation_id, payload.volunteer_id, payload.scheduled_at, current_user
    )


@router.get("", response_model=list[PickupTaskOut])
async def list_pickup_tasks(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Volunteers see only their assigned tasks; NGO staff see their organization's tasks."""
    query = select(PickupTask)
    if current_user.role == RoleName.VOLUNTEER:
        query = query.where(PickupTask.volunteer_id == current_user.id)
    elif current_user.role not in (RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(query.order_by(PickupTask.scheduled_at.asc().nullslast()))
    return result.scalars().all()


@router.patch("/{task_id}/status", response_model=PickupTaskOut)
async def update_status(
    task_id: uuid.UUID,
    payload: PickupTaskStatusUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.VOLUNTEER, RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    task = await get_pickup_task_or_404(db, task_id)
    return await update_pickup_task_status(db, task, payload.new_status, current_user, note=payload.note)
