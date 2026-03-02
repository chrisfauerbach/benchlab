"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from benchlab import __version__
from benchlab.api.dependencies import cleanup, get_storage
from benchlab.api.routers import batches, health, metrics, models, prompts, runs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    storage = get_storage()
    await storage.ensure_index()
    yield
    await cleanup()


def create_app() -> FastAPI:
    app = FastAPI(
        title="BenchLab API",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(batches.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(prompts.router, prefix="/api")
    app.include_router(metrics.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")

    return app


app = create_app()
