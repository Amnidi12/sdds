import uuid
from pydantic import BaseModel

class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None

class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    is_verified: bool
    is_active: bool

    model_config = {"from_attributes": True}
