#!/usr/bin/env python3
"""
Test SMTP STARTTLS login only (no email sent).

From repo root:
  .venv/bin/python scripts/smtp_probe.py

Exits 0 on success, 1 on auth/network failure. Does not print your password.
"""

from __future__ import annotations

import smtplib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402


def main() -> int:
    s = get_settings()
    if not s.smtp_host or not s.smtp_user:
        print("SMTP_HOST / SMTP_USER missing in environment.")
        return 1
    pw = s.smtp_password or ""
    print("Host:", s.smtp_host, " Port:", s.smtp_port, " STARTTLS:", s.smtp_use_tls)
    print("User:", s.smtp_user)
    print("Password length (after normalisation):", len(pw))
    try:
        if s.smtp_use_tls:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(s.smtp_user, pw)
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as smtp:
                smtp.login(s.smtp_user, pw)
    except smtplib.SMTPAuthenticationError as e:
        err = e.smtp_error.decode(errors="replace") if e.smtp_error else ""
        print("AUTH FAILED:", e.smtp_code, err[:300])
        return 1
    except OSError as e:
        print("NETWORK FAILED:", e)
        return 1
    print("LOGIN OK (Google/your SMTP accepted the username and password).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
