from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

# Always load `.env` from the repository root, not the process cwd. Otherwise
# starting uvicorn from `app/` or an IDE workspace makes `env_file=".env"`
# point at the wrong file and SMTP uses empty/wrong credentials (535 from Google).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_DOTENV = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_DOTENV if _REPO_DOTENV.is_file() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NewsletterService"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # Set via DATABASE_URL in .env (e.g. same as Prisma). postgresql:// is normalized in get_async_database_url().
    database_url: str = "postgresql+asyncpg://localhost:5432/app"

    # Comma-separated origins for CORS (e.g. Vite on port 5173). Empty disables CORS middleware.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # If true, serve the built Vite app from `frontend/dist` at `/` (useful after `npm run build` in /frontend).
    serve_dashboard: bool = False

    # Outbound email (newsletter outreach). When email_send_enabled is false, /newsletter/email/send returns 503.
    email_send_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "WDW Operations"

    # Public SPA URL for job deep links in newsletter emails (hash routes: /#/jobs/{publicSlug-or-id})
    public_job_site_url: str = "https://www.worlddiveweb.com"

    # (Newsletter header is text-only — no logo/env needed for images.)
    @classmethod
    def _normalize_smtp_password(cls, v: object) -> object:
        # Google app passwords are 16 chars; Google often shows them as four groups with spaces,
        # but SMTP auth must send without spaces or Gmail returns 535.
        if isinstance(v, str) and v.strip():
            return "".join(v.split())
        return v

    @field_validator("smtp_user", "smtp_from_email", mode="before")
    @classmethod
    def _strip_email_fields(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Default pydantic-settings order is init → env → dotenv → secrets. Merging
        # makes OS env override the repo .env file, so a stale exported SMTP_PASSWORD
        # in the shell always wins and Gmail returns 535. Apply dotenv before env so
        # `.env` wins over process environment for local development.
        #
        # NOTE: For Docker/K8s, a variable set in both `.env` and the container env
        # will use the value from `.env`. Omit secrets from the image `.env` if you
        # rely on `-e` for production overrides.
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


def get_settings() -> Settings:
    # No caching: SMTP and other .env values must update without a full process restart
    # after developers edit .env (uvicorn --reload does not watch .env).
    return Settings()


def get_cors_origins() -> list[str]:
    raw = get_settings().cors_origins.strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_async_database_url() -> str:
    u = get_settings().database_url.strip()
    if u.startswith(("postgresql+asyncpg://", "postgres+asyncpg://")):
        return u
    if u.startswith("postgresql://"):
        return "postgresql+asyncpg://" + u.removeprefix("postgresql://")
    if u.startswith("postgres://"):
        return "postgresql+asyncpg://" + u.removeprefix("postgres://")
    return u
