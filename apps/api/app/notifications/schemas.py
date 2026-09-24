import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str | None
    event_type: str
    is_read: bool
    link: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
