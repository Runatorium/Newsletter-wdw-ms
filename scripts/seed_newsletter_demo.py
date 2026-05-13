#!/usr/bin/env python3
"""
Load synthetic jobs and divers for testing newsletter / certification matching.

Run from the repository root (with .env / DATABASE_URL set):

    .venv/bin/python scripts/seed_newsletter_demo.py

Remove previously seeded rows, then insert fresh data:

    .venv/bin/python scripts/seed_newsletter_demo.py --clean

Options:
    --jobs N   number of job posts (default 50)
    --divers N number of divers (default 50)
    --seed S   RNG seed for reproducible data (default 42)
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.db.session import get_async_session_maker  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.diver import Diver  # noqa: E402
from app.models.job import Job  # noqa: E402

SEED_DIVER_EMAIL = "seed-diver-{}@newsletter-seed.test"
SEED_JOB_CONTACT = "seed-meta@newsletter-seed.test"
SEED_COMPANY_EMAIL = "seed-employer@newsletter-seed.test"

# Strings must match the shape used on real job rows (PROVIDER:Title).
CERT_POOL = [
    "OPITO:BOSIET (Basic Offshore Safety Induction & Emergency Training)",
    "OPITO:HUET (Helicopter Underwater Escape Training)",
    "IMCA:Diver Medic Technician (DMT)",
    "IMCA:Surface Supplied Offshore Air Diver",
    "IMCA:Offshore Air Diver",
    "GWO:Basic Safety Training (BST)",
    "GWO:Advanced Rescue Training (ART)",
    "DCBC:Commercial Diver (Inshore)",
    "HSE:Commercial Diver Medical",
    "NFPA:Rescue Technician I",
]

LOCATIONS = [
    "North Sea",
    "Saudi Arabia — Aramco",
    "Gulf of Mexico",
    "Mediterranean",
    "Singapore",
    "Brazil — pre-salt",
    "Norway",
    "UK — Aberdeen",
    None,
]


def _cert_to_upload_dict(cert_line: str, rng: random.Random, idx: int) -> dict:
    prov, _, title = cert_line.partition(":")
    return {
        "providerName": prov.strip(),
        "courseTitle": title.strip(),
        "verified": rng.random() > 0.4,
        "uploadedAt": int(datetime.now(UTC).timestamp() * 1000) - idx * 86_400_000,
        "code": f"SEED-{rng.randint(1000, 9999)}",
        "filename": f"seed-cert-{idx}.pdf",
    }


async def _ensure_companies(session) -> list[int]:
    r = await session.execute(select(Company.id).limit(20))
    existing = [row[0] for row in r.all()]
    if existing:
        return existing

    c = Company(
        company="Newsletter Seed Employer",
        email=SEED_COMPANY_EMAIL,
        role="company",
        email_verified=True,
        phone="+1-555-0100",
        address="1 Seed Wharf",
        website="https://seed.example",
        description="Auto-created for newsletter demo seeding.",
    )
    session.add(c)
    await session.flush()
    return [c.id]


async def _clean_seed_rows(session) -> None:
    await session.execute(
        delete(Diver).where(Diver.email.like("seed-diver-%@newsletter-seed.test"))
    )
    await session.execute(delete(Job).where(Job.contact_email == SEED_JOB_CONTACT))


async def seed(
    n_jobs: int,
    n_divers: int,
    rng: random.Random,
    *,
    clean: bool,
) -> None:
    sm = get_async_session_maker()
    async with sm() as session:
        if clean:
            await _clean_seed_rows(session)
            await session.commit()

        company_ids = await _ensure_companies(session)
        await session.commit()

        now = datetime.now(UTC).replace(tzinfo=None)
        jobs: list[Job] = []

        for i in range(n_jobs):
            n_certs = rng.randint(1, min(5, len(CERT_POOL)))
            job_certs = rng.sample(CERT_POOL, n_certs)
            created = now - timedelta(days=rng.randint(0, 21), hours=rng.randint(0, 23))

            j = Job(
                company_id=company_ids[i % len(company_ids)],
                title=f"[SEED] Offshore / diving role #{i + 1:02d}",
                description="Synthetic posting for newsletter and certification matching tests.",
                location=rng.choice(LOCATIONS),
                requirements=[],
                status="active",
                applications=[],
                created_at=created,
                updated_at=now,
                job_type=rng.choice(["full-time", "contract", "rotational"]),
                role=rng.choice(["Air Diver", "Sat Diver", "Supervisor", "DMT"]),
                salary=str(180 + rng.randint(0, 220)),
                certifications=job_certs,
                is_external=False,
                contact_email=SEED_JOB_CONTACT,
                positions_payload=[
                    {
                        "role": "Commercial Diver",
                        "type": "full-time",
                        "title": "Commercial Diver",
                        "salary": str(200 + rng.randint(0, 100)),
                    }
                ],
            )
            jobs.append(j)
            session.add(j)

        await session.flush()

        # Build diver certs: mix of subsets so match scores vary (0% .. 100% vs random job unions).
        all_job_certs_union: list[str] = []
        for j in jobs:
            if isinstance(j.certifications, list):
                for c in j.certifications:
                    s = str(c).strip()
                    if s and s not in all_job_certs_union:
                        all_job_certs_union.append(s)

        for d in range(n_divers):
            # Bias: some divers align with union, some with random noise.
            if rng.random() < 0.35 and all_job_certs_union:
                take_n = rng.randint(
                    max(1, int(len(all_job_certs_union) * 0.5)),
                    len(all_job_certs_union),
                )
                chosen = rng.sample(all_job_certs_union, min(take_n, len(all_job_certs_union)))
            else:
                take_n = rng.randint(0, min(6, len(CERT_POOL)))
                chosen = rng.sample(CERT_POOL, take_n) if take_n else []

            diver_certs = [_cert_to_upload_dict(c, rng, d * 10 + k) for k, c in enumerate(chosen)]

            diver = Diver(
                full_name=f"Seed Diver {d + 1:02d}",
                email=SEED_DIVER_EMAIL.format(f"{d + 1:03d}"),
                role="diver",
                phone=f"+1-555-{2000 + d:04d}",
                location=rng.choice(LOCATIONS),
                email_verified=rng.random() > 0.3,
                profile_verified=rng.random() > 0.6,
                certifications=diver_certs,
                documents=[],
                logbook=[],
                certification_validity={},
                medical_visits=[],
                created_at=now,
                updated_at=now,
            )
            session.add(diver)

        await session.commit()

    print(
        f"Seeded {n_jobs} jobs (contactEmail={SEED_JOB_CONTACT!r}) and "
        f"{n_divers} divers (*@newsletter-seed.test)."
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jobs", type=int, default=50, help="Number of job posts")
    p.add_argument("--divers", type=int, default=50, help="Number of divers")
    p.add_argument("--seed", type=int, default=42, help="RNG seed")
    p.add_argument(
        "--clean",
        action="store_true",
        help="Delete previously seeded jobs/divers before inserting",
    )
    args = p.parse_args()
    rng = random.Random(args.seed)
    asyncio.run(seed(args.jobs, args.divers, rng, clean=args.clean))


if __name__ == "__main__":
    main()
