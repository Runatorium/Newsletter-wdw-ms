from pydantic import BaseModel

from app.schemas.company import CompanyRead
from app.schemas.diver import DiverRead
from app.schemas.job_position import JobPositionRead


class DiverListResponse(BaseModel):
    items: list[DiverRead]
    total: int


class CompanyListResponse(BaseModel):
    items: list[CompanyRead]
    total: int


class JobPositionListResponse(BaseModel):
    items: list[JobPositionRead]
    total: int
