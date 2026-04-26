from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.filters import company_subscription_filter, diver_subscription_filter
from app.db.session import get_db
from app.models.company import Company
from app.models.company_subscription import CompanySubscription
from app.models.diver import Diver
from app.models.diver_subscription import DiverSubscription
from app.models.user import User
from app.schemas.stats import PeriodCounts
from app.schemas.subscription import (
    ActiveCompanySubscriptionListResponse,
    ActiveCompanySubscriptionRow,
    ActiveDiverSubscriptionListResponse,
    ActiveDiverSubscriptionRow,
    CompanySubscriptionRead,
    DiverSubscriptionRead,
)
from app.schemas.company import CompanyRead
from app.schemas.diver import DiverRead

router = APIRouter(tags=["dashboard"])


def _now_naive_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _count_since(
    db: AsyncSession,
    model,
    created_attr,
    since: datetime,
) -> int:
    q = select(func.count()).select_from(model).where(created_attr >= since)
    result = await db.execute(q)
    return int(result.scalar_one())


@router.get("/stats/new-users", response_model=PeriodCounts)
async def new_users_stats(db: AsyncSession = Depends(get_db)) -> PeriodCounts:
    now = _now_naive_utc()
    day = await _count_since(db, User, User.created_at, now - timedelta(days=1))
    week = await _count_since(db, User, User.created_at, now - timedelta(days=7))
    month = await _count_since(db, User, User.created_at, now - timedelta(days=30))
    return PeriodCounts(last_day=day, last_week=week, last_month=month)


@router.get("/stats/new-companies", response_model=PeriodCounts)
async def new_companies_stats(db: AsyncSession = Depends(get_db)) -> PeriodCounts:
    now = _now_naive_utc()
    day = await _count_since(db, Company, Company.created_at, now - timedelta(days=1))
    week = await _count_since(db, Company, Company.created_at, now - timedelta(days=7))
    month = await _count_since(db, Company, Company.created_at, now - timedelta(days=30))
    return PeriodCounts(last_day=day, last_week=week, last_month=month)


@router.get(
    "/subscriptions/divers/active",
    response_model=ActiveDiverSubscriptionListResponse,
)
async def list_active_diver_subscriptions(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str | None = Query(
        default=None,
        max_length=200,
        description="Search diver name, email, phone",
    ),
    plan: str | None = Query(
        default=None, max_length=100, description="Filter by plan (partial match)"
    ),
    status: str = Query(
        default="active",
        max_length=32,
        description="Subscription status, or 'all' for any status",
    ),
) -> ActiveDiverSubscriptionListResponse:
    flt = diver_subscription_filter(q=q, plan=plan, status=status)
    join_on = Diver.id == DiverSubscription.diver_id
    total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(DiverSubscription)
                .join(Diver, join_on)
                .where(flt)
            )
        ).scalar_one()
    )
    result = await db.execute(
        select(DiverSubscription)
        .join(Diver, join_on)
        .where(flt)
        .options(selectinload(DiverSubscription.diver))
        .order_by(DiverSubscription.id.desc())
        .offset(skip)
        .limit(limit)
    )
    subs = result.scalars().all()
    items = [
        ActiveDiverSubscriptionRow(
            diver=DiverRead.model_validate(s.diver),
            subscription=DiverSubscriptionRead.model_validate(s),
        )
        for s in subs
    ]
    return ActiveDiverSubscriptionListResponse(items=items, total=total)


@router.get(
    "/subscriptions/companies/active",
    response_model=ActiveCompanySubscriptionListResponse,
)
async def list_active_company_subscriptions(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str | None = Query(
        default=None,
        max_length=200,
        description="Search company name, email, phone",
    ),
    plan: str | None = Query(
        default=None, max_length=100, description="Filter by plan (partial match)"
    ),
    status: str = Query(
        default="active",
        max_length=32,
        description="Subscription status, or 'all' for any status",
    ),
) -> ActiveCompanySubscriptionListResponse:
    flt = company_subscription_filter(q=q, plan=plan, status=status)
    join_on = Company.id == CompanySubscription.company_id
    total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(CompanySubscription)
                .join(Company, join_on)
                .where(flt)
            )
        ).scalar_one()
    )
    result = await db.execute(
        select(CompanySubscription)
        .join(Company, join_on)
        .where(flt)
        .options(selectinload(CompanySubscription.company))
        .order_by(CompanySubscription.id.desc())
        .offset(skip)
        .limit(limit)
    )
    subs = result.scalars().all()
    items = [
        ActiveCompanySubscriptionRow(
            company=CompanyRead.model_validate(s.company),
            subscription=CompanySubscriptionRead.model_validate(s),
        )
        for s in subs
    ]
    return ActiveCompanySubscriptionListResponse(items=items, total=total)
