import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.donations.models import DonationCondition, DonationStatus


class DonationCreate(BaseModel):
    category_id: uuid.UUID
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    quantity: int = Field(gt=0)
    unit: str = "items"
    estimated_weight_kg: float | None = None
    condition: DonationCondition = DonationCondition.GOOD
    pickup_required: bool = True
    pickup_address: str | None = None
    preferred_pickup_at: datetime | None = None
    expiry_date: date | None = None
    notes: str | None = None


class DonationStatusUpdate(BaseModel):
    new_status: DonationStatus
    note: str | None = None
    rejection_reason: str | None = None


class DonationStatusHistoryOut(BaseModel):
    to_status: DonationStatus
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DonationOut(BaseModel):
    id: uuid.UUID
    tracking_id: str
    donor_id: uuid.UUID
    organization_id: uuid.UUID | None
    category_id: uuid.UUID
    title: str
    description: str | None
    quantity: int
    unit: str
    condition: DonationCondition
    status: DonationStatus
    pickup_required: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DonationDetailOut(DonationOut):
    status_history: list[DonationStatusHistoryOut] = []


class PublicTrackingOut(BaseModel):
    """Deliberately minimal - never exposes donor/beneficiary PII (requirement #10)."""

    tracking_id: str
    category_name: str
    status: DonationStatus
    created_at: datetime
