from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.core.config import get_cors_origins, get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()  # load .env once at startup (settings re-read per request)
    import app.models  # noqa: F401 - register ORM mappers
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    origins = get_cors_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(v1_router, prefix=settings.api_v1_prefix, tags=["v1"])

    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    if uploads_dir.is_dir():
        app.mount(
            "/uploads",
            StaticFiles(directory=str(uploads_dir)),
            name="uploads",
        )

    if settings.serve_dashboard:
        dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
        if dist.is_dir():
            app.mount("/", StaticFiles(directory=str(dist), html=True), name="dashboard")
    return app


app = create_app()
