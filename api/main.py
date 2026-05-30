from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.db import close_pool, init_pool
from api.routes import admin, cards, dashboard, stats, webhook
from bot.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_pool()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await close_pool()


app = FastAPI(title="snap-vocab", lifespan=lifespan)
app.include_router(cards.router)
app.include_router(webhook.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(stats.router)
_STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
