import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.beneficiaries.models import Beneficiary, BeneficiaryRequest
from app.beneficiaries.schemas import (
    BeneficiaryCreate,
    BeneficiaryOut,
    BeneficiaryRequestCreate,
    BeneficiaryRequestOut,
)
from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.users.models import RoleName

router = APIRouter(prefix="/api/v1/beneficiaries", tags=["beneficiaries"])


@router.post("", response_model=BeneficiaryOut, status_code=201)
async def create_beneficiary(
    payload: BeneficiaryCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organization_id and current_user.role != RoleName.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="You must belong to an organization")
    beneficiary = Beneficiary(organization_id=current_user.organization_id, **payload.model_dump())
    db.add(beneficiary)
    await db.commit()
    await db.refresh(beneficiary)
    return beneficiary


@router.get("", response_model=list[BeneficiaryOut])
async def list_beneficiaries(
    # Restricted to NGO staff only - beneficiary lists must never be public (requirement #13)
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = select(Beneficiary)
    if current_user.role != RoleName.SUPER_ADMIN:
        query = query.where(Beneficiary.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/me", response_model=BeneficiaryOut)
async def get_my_beneficiary_profile(
    current_user: CurrentUser = Depends(require_roles(RoleName.BENEFICIARY)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Beneficiary).where(Beneficiary.user_id == current_user.id))
    beneficiary = result.scalar_one_or_none()
    if not beneficiary:
        # Note: We must explicitly use a custom code if the frontend expects it, or
        # let the frontend handle the generic 404. Let's return 404.
        raise HTTPException(status_code=404, detail="Beneficiary profile not found")
    return beneficiary


@router.post("/{beneficiary_id}/requests", response_model=BeneficiaryRequestOut, status_code=201)
async def submit_request(
    beneficiary_id: uuid.UUID,
    payload: BeneficiaryRequestCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.BENEFICIARY, RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    beneficiary = (
        await db.execute(select(Beneficiary).where(Beneficiary.id == beneficiary_id))
    ).scalar_one_or_none()
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    if current_user.role == RoleName.BENEFICIARY and beneficiary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only submit requests for your own profile")

    req = BeneficiaryRequest(beneficiary_id=beneficiary_id, **payload.model_dump())
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/{beneficiary_id}/requests", response_model=list[BeneficiaryRequestOut])
async def list_requests(
    beneficiary_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN, RoleName.BENEFICIARY)
    ),
    db: AsyncSession = Depends(get_db),
):
    beneficiary = (
        await db.execute(select(Beneficiary).where(Beneficiary.id == beneficiary_id))
    ).scalar_one_or_none()
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    if current_user.role == RoleName.BENEFICIARY and beneficiary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this beneficiary's requests")
    if (
        current_user.role == RoleName.NGO_ADMIN
        and beneficiary.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")

    result = await db.execute(
        select(BeneficiaryRequest).where(BeneficiaryRequest.beneficiary_id == beneficiary_id)
    )
    return result.scalars().all()
