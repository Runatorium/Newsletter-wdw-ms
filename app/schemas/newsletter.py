from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.diver import DiverRead


class DiverCertMatchRequest(BaseModel):
    job_ids: list[int] = Field(..., min_length=1, description="Jobs to combine required certs from")


class DiverCertMatchItem(BaseModel):
    diver: DiverRead
    match_percent: float
    matched_certifications: list[str]
    missing_certifications: list[str]
    required_total: int
    matched_count: int


class DiverCertMatchResponse(BaseModel):
    """`items` = 100% certification match; `partial_items` = strictly between 0% and 100%."""

    items: list[DiverCertMatchItem]
    partial_items: list[DiverCertMatchItem]
    required_certifications: list[str]
    job_ids: list[int]
    message: str | None = None
