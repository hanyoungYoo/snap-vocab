from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.db import close_pool, init_pool
from api.routes import admin, cards, dashboard, webhook
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


@app.get("/")
async def root() -> dict:
    return {"status": "ok"}
