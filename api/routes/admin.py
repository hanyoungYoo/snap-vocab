from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import verify_api_key
from api.settings import settings
from bot import scheduler as scheduler_mod
from bot.handlers.review import run_daily_review

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/trigger-review")
async def trigger_review(_: None = Depends(verify_api_key)) -> dict:
    sent = await run_daily_review()
    return {"sent": sent}


def _llm_configured() -> bool:
    keyless = {"ollama"}
    has_key = settings.llm_api_key or (
        settings.llm_provider == "openrouter" and settings.openrouter_api_key
    )
    return bool(settings.llm_provider) and (
        settings.llm_provider in keyless or bool(has_key)
    )


def _notification_configured() -> bool:
    if settings.notification_provider == "telegram":
        return bool(settings.telegram_bot_token and settings.telegram_chat_id)
    return False


def _next_review_at() -> str | None:
    sched = scheduler_mod._scheduler  # noqa: SLF001 — internal handle, read-only
    if sched is None:
        return None
    job = sched.get_job("daily_review")
    if job is None or job.next_run_time is None:
        return None
    return job.next_run_time.isoformat()


@router.get("/status")
async def status(_: None = Depends(verify_api_key)) -> dict:
    from api.db import acquire

    db_ok = True
    try:
        async with acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        db_ok = False

    return {
        "llm": {
            "provider": settings.llm_provider or None,
            "configured": _llm_configured(),
            "extract_model": settings.extract_model,
            "review_model": settings.review_model,
        },
        "notification": {
            "provider": settings.notification_provider,
            "configured": _notification_configured(),
        },
        "scheduler": {
            "review_time": settings.review_time,
            "next_run_at": _next_review_at(),
        },
        "db": {"ok": db_ok},
    }
