from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import verify_api_key
from api.settings import settings
from bot import scheduler as scheduler_mod
from bot.handlers.review import run_daily_review

router = APIRouter(prefix="/api/admin", tags=["admin"])

_VALID_PROVIDERS = {"claude", "openrouter", "ollama"}


@router.post("/trigger-review")
async def trigger_review(_: None = Depends(verify_api_key)) -> dict:
    sent = await run_daily_review()
    return {"sent": sent}


def _llm_configured() -> bool:
    keyless = {"ollama"}
    has_key = settings.llm_api_key or (
        settings.llm_provider == "openrouter" and settings.openrouter_api_key
    )
    return bool(settings.llm_provider) and (settings.llm_provider in keyless or bool(has_key))


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


class LLMSettingsPatch(BaseModel):
    llm_provider: str | None = None
    llm_api_key: str | None = None
    extract_model: str | None = None
    review_model: str | None = None
    review_time: str | None = None
    review_max_cards: int | None = None


@router.patch("/settings")
async def patch_settings(
    patch: LLMSettingsPatch,
    _: None = Depends(verify_api_key),
) -> dict:
    if patch.llm_provider is not None and patch.llm_provider not in _VALID_PROVIDERS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid llm_provider")
    if patch.review_time is not None:
        import re  # noqa: PLC0415

        if not re.match(r"^\d{2}:\d{2}$", patch.review_time):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "review_time must be HH:MM")

    updates = patch.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(settings, key, value)

    return {"ok": True, "updated": list(updates.keys())}


@router.get("/settings")
async def get_settings(_: None = Depends(verify_api_key)) -> dict:
    return {
        "llm_provider": settings.llm_provider,
        "extract_model": settings.extract_model,
        "review_model": settings.review_model,
        "review_time": settings.review_time,
        "review_max_cards": settings.review_max_cards,
        "has_llm_api_key": bool(settings.llm_api_key),
        "has_openrouter_api_key": bool(settings.openrouter_api_key),
    }


@router.get("/status")
async def get_status(_: None = Depends(verify_api_key)) -> dict:
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
