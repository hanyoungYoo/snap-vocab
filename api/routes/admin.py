from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import verify_api_key
from bot.handlers.review import run_daily_review

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/trigger-review")
async def trigger_review(_: None = Depends(verify_api_key)) -> dict:
    sent = await run_daily_review()
    return {"sent": sent}
