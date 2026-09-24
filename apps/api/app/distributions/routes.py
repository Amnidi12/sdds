import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.distributions.schemas import (
    DeliveryProofSubmit,
    DistributionCreate,
    DistributionOut,
    DistributionStatusUpdate,
)
from app.distributions.service import (
    create_distribution,
    get_distribution_or_404,
    submit_delivery_proof,
    transition_distribution_status,
)
from app.tasks.models import Distribution
from app.users.models import RoleName

router = APIRouter(prefix="/api/v1/distributions", tags=["distributions"])


@router.post("", response_model=DistributionOut, status_code=201)
async def create_new_distribution(
    payload: DistributionCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="You must belong to an organization")
    return await create_distribution(
        db,
        current_user.organization_id,
        payload.beneficiary_id,
        payload.request_id,
        payload.volunteer_id,
        payload.items,
        current_user,
    )


@router.get("", response_model=list[DistributionOut])
async def list_distributions(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN, RoleName.VOLUNTEER)
    ),
    db: AsyncSession = Depends(get_db),
):
    query = select(Distribution)
    if current_user.role == RoleName.VOLUNTEER:
        query = query.where(Distribution.volunteer_id == current_user.id)
    elif current_user.role == RoleName.NGO_ADMIN:
        query = query.where(Distribution.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{distribution_id}/status", response_model=DistributionOut)
async def update_distribution_status(
    distribution_id: uuid.UUID,
    payload: DistributionStatusUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN, RoleName.VOLUNTEER)
    ),
    db: AsyncSession = Depends(get_db),
):
    distribution = await get_distribution_or_404(db, distribution_id)
    if current_user.role == RoleName.VOLUNTEER and distribution.volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="This distribution is not assigned to you")
    if (
        current_user.role == RoleName.NGO_ADMIN
        and distribution.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")
    return await transition_distribution_status(db, distribution, payload.new_status, current_user)


@router.post("/{distribution_id}/proof")
async def submit_proof(
    distribution_id: uuid.UUID,
    payload: DeliveryProofSubmit,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.VOLUNTEER, RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    distribution = await get_distribution_or_404(db, distribution_id)
    if current_user.role == RoleName.VOLUNTEER and distribution.volunteer_id != current_user.id:
        raise HTTPException(status_code=403, detail="This distribution is not assigned to you")
    proof = await submit_delivery_proof(
        db, distribution, payload.recipient_confirmation_name, payload.note, None, current_user
    )
    return {"message": "Delivery proof recorded", "proof_id": str(proof.id)}
