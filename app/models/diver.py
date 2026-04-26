from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _default_list() -> list[Any]:
    return []


def _default_dict() -> dict[str, Any]:
    return {}


class Diver(Base):
    """Maps to Prisma `Diver` (table `divers`)."""

    __tablename__ = "divers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column("fullName", String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String, nullable=False, default="diver", server_default=sa.text("'diver'")
    )
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    availability_from: Mapped[str | None] = mapped_column("availabilityFrom", String, nullable=True)
    availability_to: Mapped[str | None] = mapped_column("availabilityTo", String, nullable=True)
    experiences: Mapped[str | None] = mapped_column("experiences", Text, nullable=True)
    photo: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verified: Mapped[bool] = mapped_column(
        "emailVerified", Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    profile_verified: Mapped[bool] = mapped_column(
        "profileVerified", Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    profile_verified_by: Mapped[str | None] = mapped_column("profileVerifiedBy", String, nullable=True)
    profile_verified_at: Mapped[datetime | None] = mapped_column(
        "profileVerifiedAt", DateTime(timezone=False), nullable=True
    )
    profile_verification_notes: Mapped[str | None] = mapped_column(
        "profileVerificationNotes", Text, nullable=True
    )
    documents: Mapped[Any] = mapped_column(JSONB, nullable=True, default=_default_list)
    certifications: Mapped[Any] = mapped_column(JSONB, nullable=True, default=_default_list)
    logbook: Mapped[Any] = mapped_column(JSONB, nullable=True, default=_default_list)
    certification_validity: Mapped[Any] = mapped_column(
        "certificationValidity", JSONB, nullable=True, default=_default_dict
    )
    medical_visits: Mapped[Any] = mapped_column("medicalVisits", JSONB, nullable=True, default=_default_list)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    subscription: Mapped["DiverSubscription | None"] = relationship(
        "DiverSubscription", back_populates="diver", uselist=False
    )
