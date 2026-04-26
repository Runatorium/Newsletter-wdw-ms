from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

JsonList = list[Any] | None


class CompanyBase(BaseModel):
    company: str
    email: str
    role: str = "company"
    email_verified: bool = False
    documents: JsonList = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    description: str | None = None
    logo: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: str | None = None
    email: str | None = None
    role: str | None = None
    email_verified: bool | None = None
    documents: JsonList = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    description: str | None = None
    logo: str | None = None


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
