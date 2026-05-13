from __future__ import annotations

from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy import and_, or_
from sqlalchemy.sql import ColumnElement

from app.models.company import Company
from app.models.diver import Diver
from app.models.diver_subscription import DiverSubscription
from app.models.company_subscription import CompanySubscription
from app.models.job import Job


def diver_list_filter(
    *,
    q: str | None,
    email_verified: bool | None,
    profile_verified: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> ColumnElement[bool]:
    parts: list[ColumnElement[bool]] = []
    t = (q or "").strip()
    if t:
        s = f"%{t}%"
        parts.append(
            or_(
                Diver.full_name.ilike(s),
                Diver.email.ilike(s),
                Diver.phone.ilike(s),
                Diver.location.ilike(s),
            )
        )
    if email_verified is not None:
        parts.append(Diver.email_verified == email_verified)
    if profile_verified is not None:
        parts.append(Diver.profile_verified == profile_verified)
    if created_from is not None:
        parts.append(Diver.created_at >= created_from)
    if created_to is not None:
        parts.append(Diver.created_at <= created_to)
    if not parts:
        return sa.true()  # type: ignore[return-value]
    return and_(*parts)


def company_list_filter(
    *,
    q: str | None,
    email_verified: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> ColumnElement[bool]:
    parts: list[ColumnElement[bool]] = []
    t = (q or "").strip()
    if t:
        s = f"%{t}%"
        parts.append(
            or_(
                Company.company.ilike(s),
                Company.email.ilike(s),
                Company.phone.ilike(s),
                Company.address.ilike(s),
                Company.website.ilike(s),
            )
        )
    if email_verified is not None:
        parts.append(Company.email_verified == email_verified)
    if created_from is not None:
        parts.append(Company.created_at >= created_from)
    if created_to is not None:
        parts.append(Company.created_at <= created_to)
    if not parts:
        return sa.true()  # type: ignore[return-value]
    return and_(*parts)


def diver_subscription_filter(
    *,
    q: str | None,
    plan: str | None,
    status: str | None,
) -> ColumnElement[bool]:
    """Diver + DiverSubscription; requires join in query."""
    parts: list[ColumnElement[bool]] = []
    t = (q or "").strip()
    if t:
        s = f"%{t}%"
        parts.append(
            or_(
                Diver.full_name.ilike(s),
                Diver.email.ilike(s),
                Diver.phone.ilike(s),
            )
        )
    p = (plan or "").strip()
    if p:
        parts.append(DiverSubscription.plan.ilike(f"%{p}%"))
    st = (status or "").strip().lower()
    if st and st != "all":
        parts.append(DiverSubscription.status == st)
    if not parts:
        return sa.true()  # type: ignore[return-value]
    return and_(*parts)


def company_subscription_filter(
    *,
    q: str | None,
    plan: str | None,
    status: str | None,
) -> ColumnElement[bool]:
    parts: list[ColumnElement[bool]] = []
    t = (q or "").strip()
    if t:
        s = f"%{t}%"
        parts.append(
            or_(
                Company.company.ilike(s),
                Company.email.ilike(s),
                Company.phone.ilike(s),
            )
        )
    p = (plan or "").strip()
    if p:
        parts.append(CompanySubscription.plan.ilike(f"%{p}%"))
    st = (status or "").strip().lower()
    if st and st != "all":
        parts.append(CompanySubscription.status == st)
    if not parts:
        return sa.true()  # type: ignore[return-value]
    return and_(*parts)


def _naive_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso_week_start_naive_utc() -> datetime:
    n = _naive_utc_now()
    d = n.date()
    monday = d - timedelta(days=d.weekday())
    return datetime.combine(monday, datetime.min.time())


def job_position_list_filter(
    *,
    location: str | None,
    posted_from: datetime | None,
    posted_to: datetime | None,
    posted_this_week: bool = False,
) -> ColumnElement[bool]:
    parts: list[ColumnElement[bool]] = []
    loc = (location or "").strip()
    if loc:
        parts.append(Job.location.ilike(f"%{loc}%"))
    if posted_this_week:
        week_start = _iso_week_start_naive_utc()
        lower = week_start
        if posted_from is not None and posted_from > lower:
            lower = posted_from
        parts.append(Job.created_at >= lower)
    elif posted_from is not None:
        parts.append(Job.created_at >= posted_from)
    if posted_to is not None:
        parts.append(Job.created_at <= posted_to)
    if not parts:
        return sa.true()  # type: ignore[return-value]
    return and_(*parts)
