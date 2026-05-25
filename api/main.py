from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.db import close_pool, init_pool
from api.routes import cards, dashboard, webhook


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_pool()
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(title="snap-vocab", lifespan=lifespan)
app.include_router(cards.router)
app.include_router(webhook.router)
app.include_router(dashboard.router)


@app.get("/")
async def root() -> dict:
    return {"status": "ok"}
