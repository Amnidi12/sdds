from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.donations.models import DonationCategory
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/donation-categories", tags=["donation-categories"])


class DonationCategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[DonationCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonationCategory).where(DonationCategory.is_active.is_(True)))
    return result.scalars().all()
