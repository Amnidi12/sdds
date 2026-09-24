import uuid

from pydantic import BaseModel

from app.beneficiaries.models import RequestStatus


class BeneficiaryCreate(BaseModel):
    full_name: str
    phone: str | None = None
    address: str | None = None
    household_size: int | None = None
    notes: str | None = None


class BeneficiaryOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    full_name: str
    phone: str | None
    household_size: int | None

    model_config = {"from_attributes": True}
    # NOTE: address intentionally excluded from the default output schema -
    # private beneficiary data is never exposed in list views (requirement #26).


class BeneficiaryRequestCreate(BaseModel):
    category_id: uuid.UUID
    quantity_requested: int
    notes: str | None = None


class BeneficiaryRequestOut(BaseModel):
    id: uuid.UUID
    beneficiary_id: uuid.UUID
    category_id: uuid.UUID
    quantity_requested: int
    status: RequestStatus

    model_config = {"from_attributes": True}
