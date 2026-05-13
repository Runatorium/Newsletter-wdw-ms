from __future__ import annotations

from typing import Any


def _normalize(s: str) -> str:
    return " ".join(s.split()).strip().casefold()


def _job_cert_parts(required: str) -> tuple[str, str]:
    """Split `PROVIDER:Title` into provider + title; title may contain colons."""
    req = required.strip()
    if ":" in req:
        prov, _, title = req.partition(":")
        return _normalize(prov), _normalize(title)
    return "", _normalize(req)


def _diver_cert_dicts(raw: Any) -> list[dict[str, Any]]:
    if not raw or not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)]


def diver_has_certification(required: str, diver_certifications_raw: Any) -> bool:
    """
    Job certs are strings like `IMCA:Diver Medic Technician (DMT)`.
    Diver certs are dicts with providerName + courseTitle (Prisma / upload shape).
    """
    req_flat = _normalize(required.replace(":", " "))
    rp, rt = _job_cert_parts(required)
    if not rp and not rt:
        return False

    for item in _diver_cert_dicts(diver_certifications_raw):
        dp = _normalize(str(item.get("providerName") or ""))
        dt = _normalize(str(item.get("courseTitle") or ""))
        combined = _normalize(f"{item.get('providerName') or ''}:{item.get('courseTitle') or ''}")

        if req_flat and req_flat == combined:
            return True
        if rp and rt:
            if dp != rp:
                continue
            if rt == dt or rt in dt or dt in rt:
                return True
        elif rt:
            if rt == dt or rt in dt or dt in rt:
                return True

    # String-shaped diver entries (if any)
    if isinstance(diver_certifications_raw, list):
        for x in diver_certifications_raw:
            if isinstance(x, str) and _normalize(x) == _normalize(required):
                return True

    return False


def union_job_certifications(cert_lists: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for certs in cert_lists:
        for c in certs:
            t = str(c).strip()
            if not t:
                continue
            k = t.casefold()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
    return out


def certifications_from_job_field(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


def score_diver_against_required(
    required: list[str], diver_certifications_raw: Any
) -> tuple[float, list[str], list[str]]:
    if not required:
        return 100.0, [], []
    matched: list[str] = []
    missing: list[str] = []
    for r in required:
        if diver_has_certification(r, diver_certifications_raw):
            matched.append(r)
        else:
            missing.append(r)
    pct = round(100.0 * len(matched) / len(required), 2)
    return pct, matched, missing
