import json
import re

from fastapi import APIRouter, Depends, HTTPException, status

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
    if not settings.llm_provider or not settings.llm_api_key:
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
