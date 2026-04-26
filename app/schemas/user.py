from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    role: str
    email_verified: bool = False
    profile_id: int | None = None
    oauth_provider: str | None = None
    oauth_provider_id: str | None = None


class UserCreate(UserBase):
    password_hash: str | None = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str | None = None
    role: str | None = None
    password_hash: str | None = None
    email_verified: bool | None = None
    profile_id: int | None = None
    oauth_provider: str | None = None
    oauth_provider_id: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserInDB(UserRead):
    """Includes password hash — use only server-side (e.g. auth)."""

    model_config = ConfigDict(from_attributes=True)

    password_hash: str | None = None
