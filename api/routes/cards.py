import json
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

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


def _hydrate_jsonb(row: dict) -> dict:
    if isinstance(row.get("meaning"), str):
        row["meaning"] = json.loads(row["meaning"])
    if isinstance(row.get("examples"), str):
        row["examples"] = json.loads(row["examples"])
    return row


@router.post("/cards", response_model=CaptureResponse)
async def save_cards(req: CaptureRequest, _: None = Depends(verify_api_key)) -> CaptureResponse:
    # ollama needs no key; openrouter uses its own key; others require llm_api_key
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
    expression: str | None = Field(default=None, min_length=1, max_length=200)
    type: str | None = None
    level: int | None = Field(default=None, ge=0, le=10)
    next_review: date | None = None


_SORT_COLUMNS = {"updated_at", "next_review", "level", "created_at"}


@router.get("/cards")
async def list_cards(
    _: None = Depends(verify_api_key),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    q: str = Query(default="", max_length=200),
    type: str | None = Query(default=None),
    level: int | None = Query(default=None, ge=0, le=10),
    due: bool = Query(default=False),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
) -> dict:
    if type is not None and type not in _VALID_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid type")
    sort_col = sort if sort in _SORT_COLUMNS else "updated_at"
    order_sql = "ASC" if order.lower() == "asc" else "DESC"

    where: list[str] = []
    params: list = []

    def _p(value) -> str:
        params.append(value)
        return f"${len(params)}"

    if q:
        where.append(f"expression ILIKE {_p('%' + q + '%')}")
    if type:
        where.append(f"type = {_p(type)}")
    if level is not None:
        where.append(f"level = {_p(level)}")
    if due:
        where.append("next_review <= CURRENT_DATE")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    async with acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM cards {where_sql}", *params)
        rows = await conn.fetch(
            f"""SELECT id, expression, type, meaning, examples, level,
                       interval_days, next_review, created_at, updated_at
                FROM cards {where_sql}
                ORDER BY {sort_col} {order_sql}
                LIMIT {_p(limit)} OFFSET {_p(offset)}""",
            *params,
        )

    items = [_hydrate_jsonb(dict(r)) for r in rows]
    return {"items": items, "total": total}


@router.get("/cards/{card_id}")
async def get_card(card_id: int, _: None = Depends(verify_api_key)) -> dict:
    async with acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, expression, type, meaning, examples, level,
                      interval_days, next_review, created_at, updated_at
               FROM cards WHERE id = $1""",
            card_id,
        )
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "card not found")
        logs = await conn.fetch(
            """SELECT id, question_type, user_answer, correct, feedback, reviewed_at
               FROM review_logs WHERE card_id = $1
               ORDER BY reviewed_at DESC LIMIT 10""",
            card_id,
        )

    return {
        "card": _hydrate_jsonb(dict(row)),
        "review_logs": [dict(log) for log in logs],
    }


@router.patch("/cards/{card_id}")
async def update_card(
    card_id: int,
    patch: CardPatch,
    _: None = Depends(verify_api_key),
) -> dict:
    fields = patch.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no editable field")
    if "type" in fields and fields["type"] not in _VALID_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid type")

    jsonb_keys = {"meaning", "examples"}
    set_parts: list[str] = []
    values: list = []
    for i, (key, value) in enumerate(fields.items(), start=1):
        if key in jsonb_keys:
            set_parts.append(f"{key} = ${i}::jsonb")
            values.append(json.dumps(value))
        else:
            set_parts.append(f"{key} = ${i}")
            values.append(value)

    async with acquire() as conn:
        # asyncpg returns "UPDATE N" / "DELETE N"; " 0" means no row matched
        result = await conn.execute(
            f"UPDATE cards SET {', '.join(set_parts)} WHERE id = ${len(fields) + 1}",
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
