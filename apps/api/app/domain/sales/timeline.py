from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TimelineEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str  # "company_created", "contact_added", "task_completed", etc.
    entity_type: str  # "company", "contact", "activity", "task", "opportunity"
    entity_id: int
    title: str
    description: str | None = None
    company_id: int | None = None
    company_name: str | None = None
    occurred_at: datetime


class TimelineResponse(BaseModel):
    items: list[TimelineEvent]
    total: int
    page: int
    page_size: int


EventSource = Literal["company", "contact", "activity", "task", "opportunity"]
