from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.company import CompanyRead
from app.schemas.diver import DiverRead


class DiverSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    diver_id: int
    plan: str
    billing_cycle: str
    status: str
    start_date: datetime
    end_date: datetime | None
    next_billing_date: datetime | None
    referral_code: str | None = None
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_price_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CompanySubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    plan: str
    status: str
    start_date: datetime
    billing_cycle: str
    next_billing_date: datetime | None
    updated_at: datetime


class ActiveDiverSubscriptionRow(BaseModel):
    diver: DiverRead
    subscription: DiverSubscriptionRead


class ActiveCompanySubscriptionRow(BaseModel):
    company: CompanyRead
    subscription: CompanySubscriptionRead


class ActiveDiverSubscriptionListResponse(BaseModel):
    items: list[ActiveDiverSubscriptionRow]
    total: int


class ActiveCompanySubscriptionListResponse(BaseModel):
    items: list[ActiveCompanySubscriptionRow]
    total: int
