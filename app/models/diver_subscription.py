from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiverSubscription(Base):
    """Prisma `DiverSubscription` (table `diver_subscriptions`)."""

    __tablename__ = "diver_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    diver_id: Mapped[int] = mapped_column("diverId", BigInteger, ForeignKey("divers.id", ondelete="CASCADE"), unique=True)
    plan: Mapped[str] = mapped_column(String, nullable=False)
    billing_cycle: Mapped[str] = mapped_column("billingCycle", String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="active", server_default=sa.text("'active'")
    )
    start_date: Mapped[datetime] = mapped_column("startDate", DateTime(timezone=False), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column("endDate", DateTime(timezone=False), nullable=True)
    next_billing_date: Mapped[datetime | None] = mapped_column("nextBillingDate", DateTime(timezone=False), nullable=True)
    referral_code: Mapped[str | None] = mapped_column("referralCode", String, unique=True, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column("stripeCustomerId", String, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column("stripeSubscriptionId", String, nullable=True)
    stripe_price_id: Mapped[str | None] = mapped_column("stripePriceId", String, nullable=True)
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

    diver: Mapped["Diver"] = relationship("Diver", back_populates="subscription", uselist=False)
