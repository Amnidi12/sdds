import uuid

from pydantic import BaseModel

from app.tasks.models import DistributionStatus


class DistributionItemCreate(BaseModel):
    inventory_batch_id: uuid.UUID
    quantity: int


class DistributionCreate(BaseModel):
    beneficiary_id: uuid.UUID
    request_id: uuid.UUID | None = None
    volunteer_id: uuid.UUID | None = None
    items: list[DistributionItemCreate]


class DistributionStatusUpdate(BaseModel):
    new_status: DistributionStatus


class DeliveryProofSubmit(BaseModel):
    recipient_confirmation_name: str | None = None
    note: str | None = None


class DistributionOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    beneficiary_id: uuid.UUID
    volunteer_id: uuid.UUID | None
    status: DistributionStatus

    model_config = {"from_attributes": True}
