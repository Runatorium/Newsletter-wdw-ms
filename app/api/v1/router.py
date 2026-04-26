from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import dashboard_routes
from app.api.v1.filters import company_list_filter, diver_list_filter
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.diver import Diver
from app.models.company import Company
from app.schemas.diver import DiverRead
from app.schemas.listing import CompanyListResponse, DiverListResponse
from app.schemas.company import CompanyRead

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {"status": "ok", "service": settings.app_name}


@router.get("/divers", response_model=DiverListResponse)
async def list_divers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: str | None = Query(
        default=None,
        max_length=200,
        description="Case-insensitive search in full name, email, phone, location",
    ),
    email_verified: bool | None = Query(
        default=None, description="Filter by email verification"
    ),
    profile_verified: bool | None = Query(
        default=None, description="Filter by profile verification"
    ),
    created_from: datetime | None = Query(
        default=None, description="createdAt >= (ISO datetime)"
    ),
    created_to: datetime | None = Query(
        default=None, description="createdAt <= (ISO datetime)"
    ),
) -> DiverListResponse:
    where = diver_list_filter(
        q=q,
        email_verified=email_verified,
        profile_verified=profile_verified,
        created_from=created_from,
        created_to=created_to,
    )
    total = int(
        (await db.execute(select(func.count()).select_from(Diver).where(where))).scalar_one()
    )
    result = await db.execute(
        select(Diver)
        .where(where)
        .order_by(Diver.id.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.scalars().all()
    return DiverListResponse(
        items=[DiverRead.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/divers/{diver_id}", response_model=DiverRead)
async def get_diver(diver_id: int, db: AsyncSession = Depends(get_db)) -> DiverRead:
    result = await db.execute(select(Diver).where(Diver.id == diver_id))
    diver = result.scalar_one_or_none()
    if diver is None:
        raise HTTPException(status_code=404, detail="Diver not found")
    return DiverRead.model_validate(diver)


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: str | None = Query(
        default=None,
        max_length=200,
        description="Case-insensitive search in company name, email, phone, address, website",
    ),
    email_verified: bool | None = Query(
        default=None, description="Filter by email verification"
    ),
    created_from: datetime | None = Query(
        default=None, description="createdAt >= (ISO datetime)"
    ),
    created_to: datetime | None = Query(
        default=None, description="createdAt <= (ISO datetime)"
    ),
) -> CompanyListResponse:
    where = company_list_filter(
        q=q,
        email_verified=email_verified,
        created_from=created_from,
        created_to=created_to,
    )
    total = int(
        (
            await db.execute(
                select(func.count()).select_from(Company).where(where)
            )
        ).scalar_one()
    )
    result = await db.execute(
        select(Company)
        .where(where)
        .order_by(Company.id.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.scalars().all()
    return CompanyListResponse(
        items=[CompanyRead.model_validate(r) for r in rows],
        total=total,
    )


router.include_router(dashboard_routes.router)
