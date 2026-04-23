from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routex_gateway.api.admin.v1 import (
    metrics,
    profiles,
    providers,
    requests,
    rules,
    settings,
    tokens,
)
from routex_gateway.api.public.v1 import chat, embeddings, health, models, responses
from routex_gateway.core.config import get_settings
from routex_gateway.core.logging import configure_logging
from routex_gateway.services.bootstrap import initialize_database
from routex_gateway.services.runtime import RouteXRuntime
from routex_gateway.storage.db import build_engine, build_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.logs_dir)
    engine = build_engine(settings)
    session_factory = build_session_factory(settings)
    await initialize_database(session_factory, engine)
    app.state.session_factory = session_factory
    app.state.runtime = RouteXRuntime(settings=settings, session_factory=session_factory)
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="RouteX Gateway",
        version="0.2.0-alpha",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:1420", "http://127.0.0.1:1420"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(models.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(responses.router, prefix="/v1")
    app.include_router(embeddings.router, prefix="/v1")

    admin_prefix = "/api/admin/v1"
    app.include_router(providers.router, prefix=admin_prefix)
    app.include_router(profiles.router, prefix=admin_prefix)
    app.include_router(rules.router, prefix=admin_prefix)
    app.include_router(settings.router, prefix=admin_prefix)
    app.include_router(metrics.router, prefix=admin_prefix)
    app.include_router(requests.router, prefix=admin_prefix)
    app.include_router(tokens.router, prefix=admin_prefix)
    return app


app = create_app()
