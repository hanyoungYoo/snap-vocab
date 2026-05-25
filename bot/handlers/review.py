from __future__ import annotations

import json
import logging
import re

from api.db import acquire
from api.settings import settings
from bot.srs import get_question_type
from llm.base import get_llm
from notification.base import get_notification
from prompts.generate import GENERATE_SYSTEM, fill_blank_prompt, multiple_choice_prompt

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    m = re.search(r"\{[\s\S]*\}", text.strip())
    return json.loads(m.group(0)) if m else {}


async def run_daily_review() -> int:
    """Send up to N due review cards. Returns count sent."""
    async with acquire() as conn:
        cards = await conn.fetch(
            """SELECT id, expression, type, meaning, examples, level
               FROM cards
               WHERE next_review <= CURRENT_DATE
               ORDER BY next_review ASC
               LIMIT $1""",
            settings.review_max_cards,
        )

    if not cards:
        return 0

    llm = get_llm(model=settings.review_model)
    notif = get_notification()
    sent = 0

    for card in cards:
        try:
            card_d = dict(card)
            # asyncpg decodes JSONB to dict/list, but some drivers/versions return strings.
            for key in ("meaning", "examples"):
                val = card_d.get(key)
                if isinstance(val, str):
                    try:
                        card_d[key] = json.loads(val)
                    except json.JSONDecodeError:
                        card_d[key] = {} if key == "meaning" else []
            qtype = get_question_type(card_d["level"])
            prompt_fn = multiple_choice_prompt if qtype == "multiple_choice" else fill_blank_prompt
            raw = await llm.complete(GENERATE_SYSTEM, prompt_fn(card_d), max_tokens=1024)
            q = _extract_json(raw)
            if not q:
                logger.warning("card %s: LLM returned no parseable JSON, skipping", card_d["id"])
                continue

            message_id = await notif.send_question(
                {
                    "card_id": card_d["id"],
                    "type": qtype,
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "answer": q.get("answer", ""),
                }
            )

            if qtype != "multiple_choice":
                async with acquire() as conn:
                    await conn.execute(
                        """INSERT INTO pending_reviews
                             (message_id, card_id, correct_answer, question)
                           VALUES ($1, $2, $3, $4)
                           ON CONFLICT (message_id) DO UPDATE
                             SET card_id = EXCLUDED.card_id,
                                 correct_answer = EXCLUDED.correct_answer,
                                 question = EXCLUDED.question""",
                        message_id,
                        card_d["id"],
                        q.get("answer", ""),
                        q.get("question", ""),
                    )
            sent += 1
        except Exception:
            logger.exception("card %s: failed to send review, skipping", card.get("id"))

    return sent
