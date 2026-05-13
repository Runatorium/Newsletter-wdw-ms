from __future__ import annotations

from pydantic import BaseModel, Field


class NewsletterEmailPreviewRequest(BaseModel):
    job_ids: list[int] = Field(..., min_length=1)
    diver_id: int = Field(..., description="Diver to personalize the preview (name & address)")


class NewsletterEmailPreviewResponse(BaseModel):
    subject: str
    body_html: str
    body_text: str
    to_email: str
    to_name: str
    job_count: int


class NewsletterEmailSendRequest(BaseModel):
    job_ids: list[int] = Field(..., min_length=1)
    diver_ids: list[int] = Field(..., min_length=1)


class NewsletterEmailSendError(BaseModel):
    diver_id: int
    detail: str


class NewsletterEmailSendResponse(BaseModel):
    sent: int
    errors: list[NewsletterEmailSendError]
