from __future__ import annotations

import json
import re

from api.db import acquire
from api.settings import settings
from bot.srs import calculate_next_review, get_question_type
from llm.base import get_llm
from notification.base import get_notification
from prompts.grade import GRADE_SYSTEM, grade_prompt


def _extract_json(text: str) -> dict:
    m = re.search(r"\{[\s\S]*\}", text.strip())
    return json.loads(m.group(0)) if m else {}


async def _update_card_and_log(
    card: dict, correct: bool, user_answer: str, feedback: str, qtype: str
) -> None:
    new_level, new_interval = calculate_next_review(card["level"], correct, card["interval_days"])
    async with acquire() as conn:
        await conn.execute(
            """UPDATE cards
               SET level=$1, interval_days=$2,
                   next_review=CURRENT_DATE + ($2 || ' days')::interval
               WHERE id=$3""",
            new_level,
            new_interval,
            card["id"],
        )
        await conn.execute(
            """INSERT INTO review_logs (card_id, question_type, user_answer, correct, feedback)
               VALUES ($1, $2, $3, $4, $5)""",
            card["id"],
            qtype,
            user_answer,
            correct,
            feedback,
        )


async def handle_choice(card_id: int, choice: str) -> None:
    """Multiple-choice answer. No LLM call; direct compare against card expression."""
    async with acquire() as conn:
        card = await conn.fetchrow(
            "SELECT id, expression, level, interval_days FROM cards WHERE id=$1",
            card_id,
        )

    if not card:
        return

    card_d = dict(card)
    correct = choice.strip().lower() == card_d["expression"].strip().lower()
    feedback = "✅ 정답" if correct else f"❌ 정답: {card_d['expression']}"

    notif = get_notification()
    await notif.send_feedback(feedback)
    await _update_card_and_log(card_d, correct, choice, feedback, "multiple_choice")


async def handle_text_answer(reply_to_message_id: str | None, text: str) -> None:
    """Fill-blank / composition answer.

    Match via reply_to_message_id when present; otherwise fall back to the most
    recent pending_reviews row (single-user assumption).
    DB connection is released before the LLM call to avoid holding a pool
    connection during a multi-second network round-trip.
    """
    async with acquire() as conn:
        if reply_to_message_id:
            pending = await conn.fetchrow(
                "SELECT * FROM pending_reviews WHERE message_id=$1",
                reply_to_message_id,
            )
        else:
            pending = await conn.fetchrow(
                "SELECT * FROM pending_reviews ORDER BY created_at DESC LIMIT 1"
            )
        if not pending:
            return
        card = await conn.fetchrow(
            "SELECT id, expression, meaning, level, interval_days FROM cards WHERE id=$1",
            pending["card_id"],
        )

    if not card:
        return

    pending_d = dict(pending)
    card_d = dict(card)

    # DB connection released above; LLM call happens outside the acquire block.
    llm = get_llm(model=settings.review_model)
    raw = await llm.complete(
        GRADE_SYSTEM,
        grade_prompt(card_d, pending_d["question"], pending_d["correct_answer"], text),
        max_tokens=512,
    )
    result = _extract_json(raw)
    correct = bool(result.get("correct", False))
    feedback_text = result.get("feedback", "")
    better = result.get("better_expression", "")

    msg = ("✅ " if correct else "❌ ") + feedback_text
    if better:
        msg += f"\n💡 {better}"

    notif = get_notification()
    await notif.send_feedback(msg)
    await _update_card_and_log(
        card_d,
        correct,
        text,
        feedback_text,
        get_question_type(card_d["level"]),
    )

    async with acquire() as conn:
        await conn.execute(
            "DELETE FROM pending_reviews WHERE message_id=$1", pending_d["message_id"]
        )
