import json
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from api.db import acquire
from api.deps import verify_api_key
from api.models.card import CaptureRequest, CaptureResponse
from api.settings import settings
from llm.base import get_llm
from prompts.extract import EXTRACT_SYSTEM, extract_prompt

router = APIRouter(prefix="/api", tags=["cards"])

_VALID_TYPES = {"word", "idiom", "grammar"}


def _parse_cards(raw: str) -> list[dict]:
    """Extract a JSON array from LLM output, tolerating markdown fences."""
    text = raw.strip()
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [c for c in data if isinstance(c, dict) and c.get("type") in _VALID_TYPES]


@router.post("/cards", response_model=CaptureResponse)
async def save_cards(req: CaptureRequest, _: None = Depends(verify_api_key)) -> CaptureResponse:
    # ollama는 API 키 불필요; openrouter는 자체 키 사용; 나머지는 llm_api_key 필수
    keyless = {"ollama"}
    has_key = settings.llm_api_key or (
        settings.llm_provider == "openrouter" and settings.openrouter_api_key
    )
    if not settings.llm_provider or (settings.llm_provider not in keyless and not has_key):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LLM_PROVIDER / LLM_API_KEY not configured",
        )

    llm = get_llm(model=settings.extract_model)
    raw = await llm.complete(EXTRACT_SYSTEM, extract_prompt(req.text))
    cards = _parse_cards(raw)

    saved: list[str] = []
    duplicates: list[str] = []

    async with acquire() as conn:
        for card in cards:
            existing = await conn.fetchrow(
                "SELECT id FROM cards WHERE expression = $1 AND type = $2",
                card["expression"],
                card["type"],
            )
            if existing:
                new_examples = [
                    e
                    for e in card.get("examples", [])
                    if isinstance(e, dict) and e.get("source") == "generated"
                ]
                if new_examples:
                    await conn.execute(
                        "UPDATE cards SET examples = examples || $1::jsonb WHERE id = $2",
                        json.dumps(new_examples),
                        existing["id"],
                    )
                duplicates.append(card["expression"])
            else:
                await conn.execute(
                    """INSERT INTO cards (expression, type, meaning, examples)
                       VALUES ($1, $2, $3::jsonb, $4::jsonb)""",
                    card["expression"],
                    card["type"],
                    json.dumps(card.get("meaning", {})),
                    json.dumps(card.get("examples", [])),
                )
                saved.append(card["expression"])

    return CaptureResponse(saved=saved, duplicates=duplicates)


class CardPatch(BaseModel):
    meaning: dict | None = None
    examples: list | None = None


@router.get("/cards")
async def list_cards(
    _: None = Depends(verify_api_key),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    async with acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, expression, type, meaning, examples, level,
                      interval_days, next_review, created_at, updated_at
               FROM cards ORDER BY updated_at DESC LIMIT $1 OFFSET $2""",
            limit,
            offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM cards")

    items = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("meaning"), str):
            d["meaning"] = json.loads(d["meaning"])
        if isinstance(d.get("examples"), str):
            d["examples"] = json.loads(d["examples"])
        items.append(d)
    return {"items": items, "total": total}


@router.patch("/cards/{card_id}")
async def update_card(
    card_id: int,
    patch: CardPatch,
    _: None = Depends(verify_api_key),
) -> dict:
    fields = {k: v for k, v in patch.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no editable field")
    sets = ", ".join(f"{k} = ${i + 1}::jsonb" for i, k in enumerate(fields))
    values = [json.dumps(v) for v in fields.values()]
    async with acquire() as conn:
        # asyncpg returns "UPDATE N" / "DELETE N"; " 0" means no row matched
        result = await conn.execute(
            f"UPDATE cards SET {sets} WHERE id = ${len(fields) + 1}",
            *values,
            card_id,
        )
    if result.endswith(" 0"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "card not found")
    return {"ok": True}


@router.delete("/cards/{card_id}")
async def delete_card(card_id: int, _: None = Depends(verify_api_key)) -> dict:
    async with acquire() as conn:
        # asyncpg returns "DELETE N"; " 0" means no row matched
        result = await conn.execute("DELETE FROM cards WHERE id = $1", card_id)
    if result.endswith(" 0"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "card not found")
    return {"ok": True}
