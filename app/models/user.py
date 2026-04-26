from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Maps to Prisma `User` (table `users`)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column("passwordHash", String, nullable=True)
    email_verified: Mapped[bool] = mapped_column(
        "emailVerified", Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    profile_id: Mapped[int | None] = mapped_column("profileId", BigInteger, nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column("oauthProvider", String, nullable=True)
    oauth_provider_id: Mapped[str | None] = mapped_column("oauthProviderId", String, nullable=True)
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
