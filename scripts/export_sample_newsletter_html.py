#!/usr/bin/env python3
"""Write uploads/sample_newsletter_email.html — same HTML as the live email template."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.newsletter_mail import render_newsletter_email  # noqa: E402

BASE = "https://www.worlddiveweb.com"
settings = get_settings()

_, html, _ = render_newsletter_email(
    diver_full_name="Moreno",
    diver_email="your.email@gmail.com",
    jobs=[
        {
            "id": 11,
            "public_slug": "air-diver-79dc208e11",
            "title": "Air Diver",
            "company_name": "WorldDiveWeb",
            "location": "UAE",
        },
        {
            "id": 9,
            "public_slug": "dmt-diver-a5b6b719a9",
            "title": "Dmt Diver",
            "company_name": "WorldDiveWeb",
            "location": "UAE",
        },
    ],
    job_site_base_url=settings.public_job_site_url or BASE,
)

out = ROOT / "uploads" / "sample_newsletter_email.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out}")
