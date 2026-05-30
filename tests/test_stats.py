from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

API_KEY = "test-secret"
HEADERS = {"X-API-Key": API_KEY}


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean(clean_tables):  # noqa: PT004
    yield


async def _seed(db_pool):
    async with db_pool.acquire() as conn:
        card_id = await conn.fetchval(
            """INSERT INTO cards (expression, type, meaning, examples, level)
               VALUES ('foo', 'word', '{}'::jsonb, '[]'::jsonb, 2) RETURNING id"""
        )
        await conn.execute(
            """INSERT INTO review_logs (card_id, question_type, correct)
               VALUES ($1, 'fill_blank', true),
                      ($1, 'fill_blank', false)""",
            card_id,
        )
    return card_id


@pytest.mark.asyncio
async def test_stats_summary_requires_auth(client: AsyncClient):
    r = await client.get("/api/stats/summary")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_stats_summary_empty(client: AsyncClient):
    r = await client.get("/api/stats/summary", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["due_today"] == 0
    assert data["accuracy_7d"] == 0
    assert data["new_7d"] == 0
    assert data["levels"] == []


@pytest.mark.asyncio
async def test_stats_summary_with_data(client: AsyncClient, db_pool):
    await _seed(db_pool)
    r = await client.get("/api/stats/summary", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["due_today"] == 1
    assert data["new_7d"] == 1
    assert data["accuracy_7d"] == 50.0
    assert data["levels"] == [{"level": 2, "n": 1}]


@pytest.mark.asyncio
async def test_stats_timeseries_shape(client: AsyncClient, db_pool):
    await _seed(db_pool)
    r = await client.get("/api/stats/timeseries?days=7", headers=HEADERS)
    assert r.status_code == 200
    points = r.json()["points"]
    assert len(points) == 7
    today = points[-1]
    assert today["reviews"] == 2
    assert today["correct"] == 1
    assert today["accuracy"] == 50.0


@pytest.mark.asyncio
async def test_admin_status(client: AsyncClient, monkeypatch):
    from api import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "llm_provider", "claude")
    monkeypatch.setattr(settings_module.settings, "llm_api_key", "x")
    monkeypatch.setattr(settings_module.settings, "telegram_bot_token", "t")
    monkeypatch.setattr(settings_module.settings, "telegram_chat_id", "c")
    r = await client.get("/api/admin/status", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["llm"]["provider"] == "claude"
    assert data["llm"]["configured"] is True
    assert data["notification"]["provider"] == "telegram"
    assert data["notification"]["configured"] is True
    assert data["db"]["ok"] is True
    assert "review_time" in data["scheduler"]


@pytest.mark.asyncio
async def test_admin_status_requires_auth(client: AsyncClient):
    r = await client.get("/api/admin/status")
    assert r.status_code == 401
