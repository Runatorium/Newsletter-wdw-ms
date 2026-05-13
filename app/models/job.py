from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    """Maps to Prisma `Job` (table `jobs`)."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column("companyId", BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    public_slug: Mapped[str | None] = mapped_column("publicSlug", Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[Any] = mapped_column(JSONB, nullable=True)
    image_url: Mapped[str | None] = mapped_column("imageUrl", Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    applications: Mapped[Any] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=False), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime(timezone=False), nullable=False
    )
    job_type: Mapped[str | None] = mapped_column("type", Text, nullable=True)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(
        "startDate", DateTime(timezone=False), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        "endDate", DateTime(timezone=False), nullable=True
    )
    certifications: Mapped[Any] = mapped_column(JSONB, nullable=True)
    is_external: Mapped[bool] = mapped_column(
        "isExternal", Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    original_post_url: Mapped[str | None] = mapped_column("originalPostUrl", Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column("contactEmail", Text, nullable=True)
    positions_payload: Mapped[Any] = mapped_column("positions", JSONB, nullable=False)
