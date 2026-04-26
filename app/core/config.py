from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Newsletter WDW"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # Set via DATABASE_URL in .env (e.g. same as Prisma). postgresql:// is normalized in get_async_database_url().
    database_url: str = "postgresql+asyncpg://localhost:5432/app"

    # Comma-separated origins for CORS (e.g. Vite on port 5173). Empty disables CORS middleware.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # If true, serve the built Vite app from `frontend/dist` at `/` (useful after `npm run build` in /frontend).
    serve_dashboard: bool = False


@lru_cache
def get_settings() -> Settings:
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
