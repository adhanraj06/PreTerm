from pathlib import Path
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.init_db import initialize_database
from app.db.seed import seed_demo_user, seed_markets
from app.db.session import SessionLocal
from app.services.sentiment_service import ensure_vader_ready
from app.static import attach_frontend


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    ensure_vader_ready()

    with SessionLocal() as db:
        seed_demo_user(db)
        seed_markets(db)

    yield


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    dist_dir = (Path(__file__).resolve().parents[2] / settings.frontend_dist_dir).resolve()
    if settings.serve_frontend and dist_dir.exists():
        attach_frontend(app, dist_dir)

    return app


app = create_application()
