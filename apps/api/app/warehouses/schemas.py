import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.warehouses.models import InventoryMovementType


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    address: str | None = None


class WarehouseOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    address: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class InventoryReceiveRequest(BaseModel):
    """Used when warehouse staff receive+verify a picked-up donation, creating stock."""

    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)
    storage_location: str | None = None
    expiry_date: date | None = None


class InventoryBatchOut(BaseModel):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    donation_id: uuid.UUID
    category_id: uuid.UUID
    quantity_available: int
    quantity_reserved: int
    storage_location: str | None
    expiry_date: date | None

    model_config = {"from_attributes": True}


class InventoryMovementOut(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    movement_type: InventoryMovementType
    quantity: int
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
