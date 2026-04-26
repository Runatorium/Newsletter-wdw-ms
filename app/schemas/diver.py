from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

JsonList = list[Any] | None
JsonObject = dict[str, Any] | None


class DiverBase(BaseModel):
    full_name: str
    email: str
    role: str = "diver"
    phone: str | None = None
    location: str | None = None
    availability_from: str | None = None
    availability_to: str | None = None
    experiences: str | None = None
    photo: str | None = None
    email_verified: bool = False
    profile_verified: bool = False
    profile_verified_by: str | None = None
    profile_verified_at: datetime | None = None
    profile_verification_notes: str | None = None
    documents: JsonList = None
    certifications: JsonList = None
    logbook: JsonList = None
    certification_validity: JsonObject = None
    medical_visits: JsonList = None


class DiverCreate(DiverBase):
    pass


class DiverUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str | None = None
    email: str | None = None
    role: str | None = None
    phone: str | None = None
    location: str | None = None
    availability_from: str | None = None
    availability_to: str | None = None
    experiences: str | None = None
    photo: str | None = None
    email_verified: bool | None = None
    profile_verified: bool | None = None
    profile_verified_by: str | None = None
    profile_verified_at: datetime | None = None
    profile_verification_notes: str | None = None
    documents: JsonList = None
    certifications: JsonList = None
    logbook: JsonList = None
    certification_validity: JsonObject = None
    medical_visits: JsonList = None


class DiverRead(DiverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
