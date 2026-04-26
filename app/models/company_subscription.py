from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompanySubscription(Base):
    """Prisma `CompanySubscription` (table `company_subscriptions`). No `createdAt` in Prisma schema."""

    __tablename__ = "company_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column("companyId", BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), unique=True)
    plan: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="active", server_default=sa.text("'active'")
    )
    start_date: Mapped[datetime] = mapped_column("startDate", DateTime(timezone=False), nullable=False)
    billing_cycle: Mapped[str] = mapped_column("billingCycle", String, nullable=False)
    next_billing_date: Mapped[datetime | None] = mapped_column("nextBillingDate", DateTime(timezone=False), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship("Company", back_populates="subscription", uselist=False)
