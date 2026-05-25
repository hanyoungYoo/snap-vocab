from __future__ import annotations

import json

import pytest


class _StubLLM:
    def __init__(self, payload: dict):
        self.payload = payload
        self.calls = 0

    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str:
        self.calls += 1
        return json.dumps(self.payload)


class _StubNotification:
    def __init__(self, message_id: str = "42"):
        self.message_id = message_id
        self.questions: list[dict] = []
        self.feedbacks: list[str] = []

    async def send_question(self, question: dict) -> str:
        self.questions.append(question)
        return self.message_id

    async def send_feedback(self, text: str) -> None:
        self.feedbacks.append(text)

    async def send_text(self, text: str) -> None:
        self.feedbacks.append(text)


@pytest.fixture
def patch_llm_and_notif(monkeypatch):
    def _apply(payload: dict, message_id: str = "42"):
        from bot.handlers import review as review_mod

        llm = _StubLLM(payload)
        notif = _StubNotification(message_id=message_id)
        monkeypatch.setattr(review_mod, "get_llm", lambda *a, **k: llm)
        monkeypatch.setattr(review_mod, "get_notification", lambda *a, **k: notif)
        return llm, notif

    return _apply


async def _insert_due_card(db_pool, *, level: int = 0) -> int:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO cards
                 (expression, type, meaning, examples, level, interval_days, next_review)
               VALUES ($1, 'word', $2::jsonb, $3::jsonb, $4, 1, CURRENT_DATE)
               RETURNING id""",
            "ubiquitous",
            json.dumps({"core": "everywhere"}),
            json.dumps([{"sentence": "Smartphones are ubiquitous."}]),
            level,
        )
        return row["id"]


async def test_trigger_review_requires_api_key(client):
    resp = await client.post("/api/admin/trigger-review")
    assert resp.status_code == 422  # Missing required header


async def test_trigger_review_rejects_bad_key(client):
    resp = await client.post("/api/admin/trigger-review", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


async def test_trigger_review_multiple_choice_sends_and_no_pending(
    client, db_pool, patch_llm_and_notif
):
    await _insert_due_card(db_pool, level=0)
    llm, notif = patch_llm_and_notif(
        {
            "question": "Which one means 'everywhere'?",
            "options": ["ubiquitous", "rare", "scarce", "narrow"],
            "answer": "ubiquitous",
            "hint": "",
        }
    )

    resp = await client.post("/api/admin/trigger-review", headers={"X-API-Key": "test-secret"})
    assert resp.status_code == 200
    assert resp.json() == {"sent": 1}
    assert llm.calls == 1
    assert len(notif.questions) == 1
    assert notif.questions[0]["type"] == "multiple_choice"

    async with db_pool.acquire() as conn:
        pending = await conn.fetch("SELECT * FROM pending_reviews")
    assert pending == []


async def test_trigger_review_fill_blank_creates_pending(client, db_pool, patch_llm_and_notif):
    await _insert_due_card(db_pool, level=4)
    _, notif = patch_llm_and_notif(
        {
            "question": "Smartphones are ___ today.",
            "answer": "ubiquitous",
            "hint": "",
        },
        message_id="100",
    )

    resp = await client.post("/api/admin/trigger-review", headers={"X-API-Key": "test-secret"})
    assert resp.status_code == 200
    assert resp.json() == {"sent": 1}
    assert notif.questions[0]["type"] == "fill_blank"

    async with db_pool.acquire() as conn:
        pending = await conn.fetch("SELECT message_id, correct_answer FROM pending_reviews")
    assert len(pending) == 1
    assert pending[0]["message_id"] == "100"
    assert pending[0]["correct_answer"] == "ubiquitous"


async def test_trigger_review_no_due_cards_returns_zero(client, patch_llm_and_notif):
    patch_llm_and_notif({"question": "x", "options": [], "answer": "x"})
    resp = await client.post("/api/admin/trigger-review", headers={"X-API-Key": "test-secret"})
    assert resp.status_code == 200
    assert resp.json() == {"sent": 0}
