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


class Company(Base):
    """Maps to Prisma `Company` (table `companies`)."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column("company", String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String, nullable=False, default="company", server_default=sa.text("'company'")
    )
    email_verified: Mapped[bool] = mapped_column(
        "emailVerified", Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    documents: Mapped[Any] = mapped_column(JSONB, nullable=True, default=_default_list)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(String, nullable=True)
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

    subscription: Mapped["CompanySubscription | None"] = relationship(
        "CompanySubscription", back_populates="company", uselist=False
    )
