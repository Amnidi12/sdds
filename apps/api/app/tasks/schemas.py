import uuid
from datetime import datetime

from pydantic import BaseModel

from app.tasks.models import PickupTaskStatus


class PickupTaskCreate(BaseModel):
    donation_id: uuid.UUID
    volunteer_id: uuid.UUID | None = None
    scheduled_at: datetime | None = None


class PickupTaskStatusUpdate(BaseModel):
    new_status: PickupTaskStatus
    note: str | None = None


class PickupTaskOut(BaseModel):
    id: uuid.UUID
    donation_id: uuid.UUID
    volunteer_id: uuid.UUID | None
    scheduled_at: datetime | None
    status: PickupTaskStatus
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
