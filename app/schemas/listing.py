from pydantic import BaseModel

from app.schemas.company import CompanyRead
from app.schemas.diver import DiverRead


class DiverListResponse(BaseModel):
    items: list[DiverRead]
    total: int


class CompanyListResponse(BaseModel):
    items: list[CompanyRead]
    total: int
