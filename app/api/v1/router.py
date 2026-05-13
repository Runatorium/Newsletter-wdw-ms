from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import dashboard_routes, newsletter_mail_routes
from app.api.v1.filters import (
    company_list_filter,
    diver_list_filter,
    job_position_list_filter,
)
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.diver import Diver
from app.models.company import Company
from app.models.job import Job
from app.schemas.diver import DiverRead
from app.schemas.listing import (
    CompanyListResponse,
    DiverListResponse,
    JobPositionListResponse,
)
from app.schemas.company import CompanyRead
from app.schemas.job_position import JobPositionRead
from app.schemas.newsletter import (
    DiverCertMatchItem,
    DiverCertMatchRequest,
    DiverCertMatchResponse,
)
from app.services.cert_matching import (
    certifications_from_job_field,
    score_diver_against_required,
    union_job_certifications,
)

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


@router.get("/job-positions", response_model=JobPositionListResponse)
async def list_job_positions(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    location: str | None = Query(
        default=None,
        max_length=200,
        description="Case-insensitive substring match on location",
    ),
    posted_from: datetime | None = Query(
        default=None, description="createdAt >= (ISO datetime); job listing date"
    ),
    posted_to: datetime | None = Query(
        default=None, description="createdAt <= (ISO datetime); job listing date"
    ),
    posted_this_week: bool = Query(
        default=False,
        description="If true, only jobs created on or after Monday 00:00 UTC of the current week",
    ),
) -> JobPositionListResponse:
    where = job_position_list_filter(
        location=location,
        posted_from=posted_from,
        posted_to=posted_to,
        posted_this_week=posted_this_week,
    )
    total = int(
        (
            await db.execute(select(func.count()).select_from(Job).where(where))
        ).scalar_one()
    )
    result = await db.execute(
        select(Job, Company.company)
        .outerjoin(Company, Job.company_id == Company.id)
        .where(where)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = [
        JobPositionRead(
            id=row.id,
            title=row.title,
            location=row.location,
            posted_at=row.created_at,
            company_name=company_name,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            certification_count=len(certifications_from_job_field(row.certifications)),
        )
        for row, company_name in result.all()
    ]
    return JobPositionListResponse(items=items, total=total)


@router.post("/newsletter/diver-cert-matches", response_model=DiverCertMatchResponse)
async def newsletter_diver_cert_matches(
    body: DiverCertMatchRequest,
    db: AsyncSession = Depends(get_db),
) -> DiverCertMatchResponse:
    unique_ids = list(dict.fromkeys(body.job_ids))
    result = await db.execute(select(Job).where(Job.id.in_(unique_ids)))
    jobs = result.scalars().all()
    found = {j.id for j in jobs}
    missing_ids = [i for i in unique_ids if i not in found]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Job id(s) not found: {missing_ids}",
        )

    cert_lists = [certifications_from_job_field(j.certifications) for j in jobs]
    required = union_job_certifications(cert_lists)
    if not required:
        return DiverCertMatchResponse(
            items=[],
            partial_items=[],
            required_certifications=[],
            job_ids=unique_ids,
            message="Selected jobs do not list any certifications on the job record; "
            "nothing to match against diver profiles.",
        )

    dres = await db.execute(select(Diver).order_by(Diver.id.desc()).limit(10_000))
    divers = dres.scalars().all()

    full: list[DiverCertMatchItem] = []
    partial: list[DiverCertMatchItem] = []
    for d in divers:
        pct, matched, missing = score_diver_against_required(required, d.certifications)
        item = DiverCertMatchItem(
            diver=DiverRead.model_validate(d),
            match_percent=pct,
            matched_certifications=matched,
            missing_certifications=missing,
            required_total=len(required),
            matched_count=len(matched),
        )
        if pct >= 100.0:
            full.append(item)
        elif pct > 0.0:
            partial.append(item)

    full.sort(key=lambda x: x.diver.full_name.casefold())
    partial.sort(key=lambda x: (-x.match_percent, x.diver.full_name.casefold()))

    return DiverCertMatchResponse(
        items=full,
        partial_items=partial,
        required_certifications=required,
        job_ids=unique_ids,
        message=None,
    )


router.include_router(dashboard_routes.router)
router.include_router(newsletter_mail_routes.router)
