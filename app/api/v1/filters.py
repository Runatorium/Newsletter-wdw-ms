from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import and_, or_
from sqlalchemy.sql import ColumnElement

from app.models.company import Company
from app.models.diver import Diver
from app.models.diver_subscription import DiverSubscription
from app.models.company_subscription import CompanySubscription


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
