from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobPositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    location: str | None
    posted_at: datetime
    company_name: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    certification_count: int = 0
