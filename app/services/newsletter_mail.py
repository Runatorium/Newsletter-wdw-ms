from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote


def _first_name(full_name: str) -> str:
    parts = (full_name or "").strip().split(None, 1)
    return parts[0] if parts else "there"


def _job_listing_url(base: str, public_slug: str | None, job_id: int) -> str:
    b = base.rstrip("/")
    seg = (public_slug or "").strip() or str(job_id)
    return f"{b}/#/jobs/{quote(seg, safe='-_.~')}"


def _job_block_html(jobs: list[dict[str, Any]], job_site_base_url: str) -> str:
    blocks: list[str] = []

    for j in jobs:
        title = html.escape(str(j.get("title") or ""), quote=True)
        company = html.escape(str(j.get("company_name") or "—"), quote=True)
        loc = j.get("location")
        loc_s = html.escape(str(loc), quote=True) if loc else ""
        jid = int(j["id"])
        ps = j.get("public_slug")
        ps_s = str(ps).strip() if ps is not None else ""
        listing_url = _job_listing_url(job_site_base_url, ps_s or None, jid)
        safe_url = html.escape(listing_url, quote=True)

        meta_rows = (
            f'<tr><td style="font-size:14px;color:#475569;line-height:1.55;padding:0 0 6px 0">'
            f'<span style="color:#64748b;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:0.04em">Company</span>'
            f"<br>{company}</td></tr>"
        )
        if loc_s:
            meta_rows += (
                f'<tr><td style="font-size:14px;color:#475569;line-height:1.55;padding:0 0 14px 0">'
                f'<span style="color:#64748b;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:0.04em">Location</span>'
                f"<br>{loc_s}</td></tr>"
            )
        meta_rows += (
            f'<tr><td style="padding:0 0 4px 0">'
            f'<a href="{safe_url}" style="color:#2563eb;font-size:14px;font-weight:600;text-decoration:underline">'
            f"View full listing</a></td></tr>"
        )

        blocks.append(
            f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 18px 0;border:1px solid #e5e7eb;border-radius:12px;background:#fafbfc">
  <tr>
    <td style="padding:20px 22px 18px 22px">
      <p style="margin:0 0 14px 0;font-size:18px;font-weight:600;color:#0f172a;line-height:1.35;letter-spacing:-0.02em">{title}</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{meta_rows}</table>
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:6px">
        <tr>
          <td>
            <a href="{safe_url}" target="_blank" rel="noopener noreferrer"
               style="display:inline-block;background:#0f172a;color:#ffffff !important;text-decoration:none;
                      padding:12px 22px;border-radius:10px;font-size:14px;font-weight:600;letter-spacing:0.01em">
              View role on WorldDiveWeb
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""
        )

    return "\n".join(blocks)


def _job_block_text(jobs: list[dict[str, Any]], job_site_base_url: str) -> str:
    lines = []
    for j in jobs:
        title = str(j.get("title") or "")
        company = str(j.get("company_name") or "—")
        loc = j.get("location")
        jid = int(j["id"])
        ps = j.get("public_slug")
        ps_s = str(ps).strip() if ps is not None else ""
        url = _job_listing_url(job_site_base_url, ps_s or None, jid)
        tail = f" — {loc}" if loc else ""
        lines.append(f"• {title} ({company}){tail}\n  {url}")
    return "\n\n".join(lines)


def render_newsletter_email(
    *,
    diver_full_name: str,
    diver_email: str,
    jobs: list[dict[str, Any]],
    job_site_base_url: str = "https://www.worlddiveweb.com",
) -> tuple[str, str, str]:
    """
    Returns (subject, body_html, body_plain).
    Each job dict: id, title, company_name, location (optional), public_slug (optional; falls back to id in URL).
    Header is text-only (no images) for reliable rendering in email clients.
    """
    if not jobs:
        raise ValueError("At least one job is required for the email body")

    greeting_name = _first_name(diver_full_name)
    n = len(jobs)
    if n == 1:
        t = str(jobs[0].get("title") or "Open role")
        subject = f"Role match: {t} | WorldDiveWeb"[:180]
    else:
        subject = f"{n} roles matched to your profile | WorldDiveWeb"[:180]

    jobs_html = _job_block_html(jobs, job_site_base_url)
    jobs_txt = _job_block_text(jobs, job_site_base_url)

    safe_greeting = html.escape(greeting_name, quote=True)
    safe_email = html.escape(diver_email, quote=True)
    site = job_site_base_url.rstrip("/")
    safe_site = html.escape(site, quote=True)

    body_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WorldDiveWeb</title>
</head>
<body style="margin:0;padding:0;background:#e8ecf1;-webkit-font-smoothing:antialiased">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e8ecf1;padding:24px 12px">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #dce3eb">
          <tr>
            <td style="padding:0;background:#0b0f14;border-bottom:1px solid #1e293b">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="width:4px;background:#2563eb;font-size:0;line-height:0">&nbsp;</td>
                  <td style="padding:22px 24px 20px 20px;font-family:Segoe UI,system-ui,-apple-system,BlinkMacSystemFont,sans-serif;text-align:left">
                    <a href="{safe_site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none">
                      <span style="font-size:22px;font-weight:700;letter-spacing:-0.03em;line-height:1.2;color:#f8fafc">WorldDiveWeb</span>
                    </a>
                    <span style="display:block;margin-top:8px;font-size:12px;font-weight:600;line-height:1.45;color:#64748b;letter-spacing:0.06em;text-transform:uppercase">
                      Linking Talent to Opportunities
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:26px 24px 8px 24px">
              <p style="margin:0 0 14px 0;font-size:16px;line-height:1.55;color:#334155">Hello {safe_greeting},</p>
              <p style="margin:0 0 22px 0;font-size:16px;line-height:1.55;color:#334155">
                Based on your profile, we believe you may be a strong fit for the following
                {"role" if n == 1 else f"{n} open roles"}. Each link opens the full listing on our platform.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 8px 24px">
              {jobs_html}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 24px 24px 24px">
              <p style="margin:0 0 12px 0;font-size:15px;line-height:1.55;color:#475569">
                If a role is a fit, continue on the listing page or reply to this message—we are happy to help.
              </p>
              <p style="margin:0 0 20px 0;font-size:15px;line-height:1.55;color:#475569">
                Kind regards,<br>
                <span style="color:#0f172a;font-weight:600">WorldDiveWeb</span>
              </p>
              <p style="margin:0;padding:16px 0 0 0;border-top:1px solid #eef1f4;font-size:11px;line-height:1.55;color:#94a3b8;text-align:left">
                Sent to {safe_email} for certification-based job matching.
                <a href="{safe_site}" style="color:#64748b;text-decoration:underline;margin-left:4px">worlddiveweb.com</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    body_text = f"""Hello {greeting_name},

Based on your profile on WorldDiveWeb, you may be a strong match for the following open role(s):

{jobs_txt}

If you are interested, open the links above for full details, or reply to this email.

Best regards,
WorldDiveWeb

---
This message was sent to {diver_email} regarding selected job postings.
{site}
"""

    return subject, body_html, body_text
