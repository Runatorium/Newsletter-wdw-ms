from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.diver import Diver
from app.models.company import Company
from app.models.job import Job
from app.schemas.newsletter_email import (
    NewsletterEmailPreviewRequest,
    NewsletterEmailPreviewResponse,
    NewsletterEmailSendError,
    NewsletterEmailSendRequest,
    NewsletterEmailSendResponse,
)
from app.services.newsletter_mail import render_newsletter_email

router = APIRouter()


async def _jobs_for_mail(
    db: AsyncSession, job_ids: list[int]
) -> tuple[list[dict], set[int]]:
    """Return job summary dicts in the same order as job_ids; set of missing ids."""
    unique = list(dict.fromkeys(job_ids))
    result = await db.execute(
        select(Job, Company.company)
        .outerjoin(Company, Job.company_id == Company.id)
        .where(Job.id.in_(unique))
    )
    rows = {row[0].id: (row[0], row[1]) for row in result.all()}
    missing = {jid for jid in unique if jid not in rows}
    ordered: list[dict] = []
    for jid in unique:
        if jid not in rows:
            continue
        job, company_name = rows[jid]
        ordered.append(
            {
                "id": job.id,
                "public_slug": job.public_slug,
                "title": job.title,
                "company_name": company_name,
                "location": job.location,
            }
        )
    return ordered, missing


def _send_one_sync(
    settings: Settings,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str,
) -> None:
    if not settings.smtp_from_email:
        raise RuntimeError("smtp_from_email is not configured")

    frm = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from_email, [to_email], msg.as_string())


@router.post("/newsletter/email/preview", response_model=NewsletterEmailPreviewResponse)
async def newsletter_email_preview(
    body: NewsletterEmailPreviewRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> NewsletterEmailPreviewResponse:
    dres = await db.execute(select(Diver).where(Diver.id == body.diver_id))
    diver = dres.scalar_one_or_none()
    if diver is None:
        raise HTTPException(status_code=404, detail="Diver not found")

    summaries, missing = await _jobs_for_mail(db, body.job_ids)
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Job id(s) not found: {sorted(missing)}",
        )
    if not summaries:
        raise HTTPException(status_code=400, detail="No valid jobs to include")

    subject, html_body, text_body = render_newsletter_email(
        diver_full_name=diver.full_name,
        diver_email=diver.email,
        jobs=summaries,
        job_site_base_url=settings.public_job_site_url,
    )
    return NewsletterEmailPreviewResponse(
        subject=subject,
        body_html=html_body,
        body_text=text_body,
        to_email=diver.email,
        to_name=diver.full_name,
        job_count=len(summaries),
    )


@router.post("/newsletter/email/send", response_model=NewsletterEmailSendResponse)
async def newsletter_email_send(
    body: NewsletterEmailSendRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> NewsletterEmailSendResponse:
    if not settings.email_send_enabled:
        raise HTTPException(
            status_code=503,
            detail="Outbound email is disabled. Set EMAIL_SEND_ENABLED=true and configure SMTP in the environment.",
        )
    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured (SMTP_HOST / SMTP_FROM_EMAIL).",
        )

    summaries, missing = await _jobs_for_mail(db, body.job_ids)
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Job id(s) not found: {sorted(missing)}",
        )
    if not summaries:
        raise HTTPException(status_code=400, detail="No valid jobs to include")

    unique_diver_ids = list(dict.fromkeys(body.diver_ids))
    dres = await db.execute(select(Diver).where(Diver.id.in_(unique_diver_ids)))
    divers = {d.id: d for d in dres.scalars().all()}
    not_found = [i for i in unique_diver_ids if i not in divers]
    if not_found:
        raise HTTPException(
            status_code=404,
            detail=f"Diver id(s) not found: {not_found}",
        )

    errors: list[NewsletterEmailSendError] = []
    sent = 0

    for did in unique_diver_ids:
        diver = divers[did]
        subject, html_body, text_body = render_newsletter_email(
            diver_full_name=diver.full_name,
            diver_email=diver.email,
            jobs=summaries,
            job_site_base_url=settings.public_job_site_url,
        )
        try:
            await asyncio.to_thread(
                _send_one_sync,
                settings,
                diver.email,
                subject,
                html_body,
                text_body,
            )
            sent += 1
        except Exception as e:  # noqa: BLE001
            errors.append(
                NewsletterEmailSendError(diver_id=did, detail=str(e)[:500]),
            )

    return NewsletterEmailSendResponse(sent=sent, errors=errors)
