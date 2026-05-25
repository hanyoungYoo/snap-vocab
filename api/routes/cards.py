import json

from fastapi import APIRouter, Depends

from api.db import acquire
from api.deps import verify_api_key
from api.models.card import CaptureRequest, CaptureResponse
from api.settings import settings

router = APIRouter(prefix="/api", tags=["cards"])


@router.post("/cards", response_model=CaptureResponse)
async def save_cards(req: CaptureRequest, _: None = Depends(verify_api_key)) -> CaptureResponse:

    if settings.llm_provider:
        raise NotImplementedError("LLM provider configured but adapter not yet implemented")

    cards = [
        {
            "expression": req.text.strip()[:100],
            "type": "word",
            "meaning": {"core": "", "nuance": ""},
            "examples": [],
        }
    ]

    saved: list[str] = []
    duplicates: list[str] = []

    async with acquire() as conn:
        for card in cards:
            row = await conn.fetchrow(
                "SELECT id FROM cards WHERE expression = $1 AND type = $2",
                card["expression"],
                card["type"],
            )
            if row:
                duplicates.append(card["expression"])
                continue
            await conn.execute(
                """INSERT INTO cards (expression, type, meaning, examples)
                   VALUES ($1, $2, $3::jsonb, $4::jsonb)""",
                card["expression"],
                card["type"],
                json.dumps(card["meaning"]),
                json.dumps(card["examples"]),
            )
            saved.append(card["expression"])

    return CaptureResponse(saved=saved, duplicates=duplicates)
