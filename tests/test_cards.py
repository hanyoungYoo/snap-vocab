import json

import pytest
import pytest_asyncio
from httpx import AsyncClient

from api import settings as settings_module
from api.routes import cards as cards_route
from llm.base import LLMBase

API_KEY = "test-secret"
HEADERS = {"X-API-Key": API_KEY}


class _FakeLLM(LLMBase):
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str:
        self.calls.append((system, user))
        return self.response


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean(clean_tables):  # noqa: PT004
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def llm_configured(monkeypatch):
    """Fill in LLM env so the 503 guard passes; restored after test."""
    monkeypatch.setattr(settings_module.settings, "llm_provider", "claude")
    monkeypatch.setattr(settings_module.settings, "llm_api_key", "test-key")
    yield


def _install_fake_llm(monkeypatch, response: str) -> _FakeLLM:
    fake = _FakeLLM(response)
    monkeypatch.setattr(cards_route, "get_llm", lambda *a, **kw: fake)
    return fake


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_invalid_api_key(client: AsyncClient):
    r = await client.post(
        "/api/cards",
        json={"text": "x"},
        headers={"X-API-Key": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_missing_api_key(client: AsyncClient):
    r = await client.post("/api/cards", json={"text": "x"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_empty_text_rejected(client: AsyncClient):
    r = await client.post("/api/cards", json={"text": ""}, headers=HEADERS)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_llm_not_configured_returns_503(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings_module.settings, "llm_provider", "")
    monkeypatch.setattr(settings_module.settings, "llm_api_key", "")
    r = await client.post("/api/cards", json={"text": "hello"}, headers=HEADERS)
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_extract_and_save_cards(client: AsyncClient, db_pool, llm_configured, monkeypatch):
    llm_response = json.dumps(
        [
            {
                "expression": "beat around the bush",
                "type": "idiom",
                "meaning": {"core": "에둘러 말하다", "nuance": "직접적인 답을 피함"},
                "examples": [
                    {"sentence": "Stop beating around the bush.", "source": "original"},
                    {"sentence": "He always beats around the bush.", "source": "generated"},
                ],
            },
            {
                "expression": "spill the beans",
                "type": "idiom",
                "meaning": {"core": "비밀을 누설하다", "nuance": "informal"},
                "examples": [
                    {"sentence": "Don't spill the beans!", "source": "generated"},
                ],
            },
        ]
    )
    _install_fake_llm(monkeypatch, llm_response)

    r = await client.post(
        "/api/cards",
        json={"text": "some english text containing idioms"},
        headers=HEADERS,
    )
    assert r.status_code == 200
    data = r.json()
    assert set(data["saved"]) == {"beat around the bush", "spill the beans"}
    assert data["duplicates"] == []

    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM cards")
        assert count == 2


@pytest.mark.asyncio
async def test_duplicate_appends_generated_examples(
    client: AsyncClient, db_pool, llm_configured, monkeypatch
):
    first = json.dumps(
        [
            {
                "expression": "hit the books",
                "type": "idiom",
                "meaning": {"core": "공부에 매진하다", "nuance": ""},
                "examples": [
                    {"sentence": "I need to hit the books.", "source": "original"},
                    {"sentence": "She hit the books all weekend.", "source": "generated"},
                ],
            }
        ]
    )
    _install_fake_llm(monkeypatch, first)
    r1 = await client.post("/api/cards", json={"text": "first"}, headers=HEADERS)
    assert r1.status_code == 200
    assert r1.json()["saved"] == ["hit the books"]

    async with db_pool.acquire() as conn:
        before = await conn.fetchval(
            "SELECT jsonb_array_length(examples) FROM cards WHERE expression = 'hit the books'"
        )

    second = json.dumps(
        [
            {
                "expression": "hit the books",
                "type": "idiom",
                "meaning": {"core": "공부에 매진하다", "nuance": ""},
                "examples": [
                    {"sentence": "Time to hit the books before finals.", "source": "generated"},
                    {"sentence": "He skipped the party to hit the books.", "source": "generated"},
                ],
            }
        ]
    )
    _install_fake_llm(monkeypatch, second)
    r2 = await client.post("/api/cards", json={"text": "second"}, headers=HEADERS)
    assert r2.status_code == 200
    assert r2.json()["saved"] == []
    assert r2.json()["duplicates"] == ["hit the books"]

    async with db_pool.acquire() as conn:
        after = await conn.fetchval(
            "SELECT jsonb_array_length(examples) FROM cards WHERE expression = 'hit the books'"
        )
    assert after == before + 2


@pytest.mark.asyncio
async def test_markdown_fenced_json_is_parsed(client: AsyncClient, llm_configured, monkeypatch):
    fenced = (
        "```json\n"
        + json.dumps(
            [
                {
                    "expression": "break the ice",
                    "type": "idiom",
                    "meaning": {"core": "어색함을 깨다", "nuance": ""},
                    "examples": [{"sentence": "Let's break the ice.", "source": "generated"}],
                }
            ]
        )
        + "\n```"
    )
    _install_fake_llm(monkeypatch, fenced)

    r = await client.post("/api/cards", json={"text": "x"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["saved"] == ["break the ice"]


@pytest.mark.asyncio
async def test_malformed_llm_response_returns_empty(
    client: AsyncClient, llm_configured, monkeypatch
):
    _install_fake_llm(monkeypatch, "sorry, I cannot help with that")

    r = await client.post("/api/cards", json={"text": "x"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json() == {"saved": [], "duplicates": []}


@pytest.mark.asyncio
async def test_dashboard_unauthorized(client: AsyncClient):
    r = await client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


@pytest.mark.asyncio
async def test_dashboard_wrong_key(client: AsyncClient):
    r = await client.get("/dashboard", cookies={"api_key": "wrong"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


@pytest.mark.asyncio
async def test_dashboard_ok(client: AsyncClient):
    r = await client.get("/dashboard", cookies={"api_key": API_KEY})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "snap-vocab" in r.text


async def _insert_card(db_pool, expression: str = "kick the bucket") -> int:
    async with db_pool.acquire() as conn:
        return await conn.fetchval(
            """INSERT INTO cards (expression, type, meaning, examples)
               VALUES ($1, 'idiom', $2::jsonb, '[]'::jsonb) RETURNING id""",
            expression,
            json.dumps({"core": "죽다", "nuance": ""}),
        )


@pytest.mark.asyncio
async def test_list_cards_empty(client: AsyncClient):
    r = await client.get("/api/cards", headers=HEADERS)
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_list_cards_returns_inserted(client: AsyncClient, db_pool):
    await _insert_card(db_pool, "break a leg")
    r = await client.get("/api/cards", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["expression"] == "break a leg"
    assert data["items"][0]["meaning"]["core"] == "죽다"


@pytest.mark.asyncio
async def test_list_cards_requires_auth(client: AsyncClient):
    r = await client.get("/api/cards", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_patch_card_meaning(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.patch(
        f"/api/cards/{card_id}",
        json={"meaning": {"core": "사망하다", "nuance": "구어"}},
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    async with db_pool.acquire() as conn:
        meaning = await conn.fetchval("SELECT meaning FROM cards WHERE id = $1", card_id)
    assert json.loads(meaning)["core"] == "사망하다"


@pytest.mark.asyncio
async def test_patch_card_level_and_next_review(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.patch(
        f"/api/cards/{card_id}",
        json={"level": 5, "next_review": "2030-01-01"},
        headers=HEADERS,
    )
    assert r.status_code == 200

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT level, next_review FROM cards WHERE id = $1", card_id
        )
    assert row["level"] == 5
    assert str(row["next_review"]) == "2030-01-01"


@pytest.mark.asyncio
async def test_patch_card_rejects_empty_body(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.patch(f"/api/cards/{card_id}", json={}, headers=HEADERS)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_patch_card_rejects_invalid_type(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.patch(
        f"/api/cards/{card_id}", json={"type": "nope"}, headers=HEADERS
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_patch_card_not_found(client: AsyncClient):
    r = await client.patch(
        "/api/cards/99999",
        json={"meaning": {"core": "x"}},
        headers=HEADERS,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_card(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.delete(f"/api/cards/{card_id}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM cards WHERE id = $1", card_id)
    assert count == 0


@pytest.mark.asyncio
async def test_delete_card_requires_auth(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    r = await client.delete(f"/api/cards/{card_id}", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_card_not_found(client: AsyncClient):
    r = await client.delete("/api/cards/99999", headers=HEADERS)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_cards_filter_by_q(client: AsyncClient, db_pool):
    await _insert_card(db_pool, "break a leg")
    await _insert_card(db_pool, "kick the bucket")
    r = await client.get("/api/cards?q=leg", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["expression"] == "break a leg"


@pytest.mark.asyncio
async def test_list_cards_filter_by_due(client: AsyncClient, db_pool):
    # one due today
    await _insert_card(db_pool, "due-today")
    # one due in the future
    async with db_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO cards (expression, type, meaning, examples, next_review)
               VALUES ('future', 'idiom', '{}'::jsonb, '[]'::jsonb,
                       CURRENT_DATE + INTERVAL '10 days')"""
        )
    r = await client.get("/api/cards?due=true", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["expression"] == "due-today"


@pytest.mark.asyncio
async def test_get_card_detail(client: AsyncClient, db_pool):
    card_id = await _insert_card(db_pool)
    async with db_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO review_logs (card_id, question_type, user_answer, correct)
               VALUES ($1, 'fill_blank', 'die', true)""",
            card_id,
        )
    r = await client.get(f"/api/cards/{card_id}", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["card"]["id"] == card_id
    assert len(data["review_logs"]) == 1
    assert data["review_logs"][0]["correct"] is True


@pytest.mark.asyncio
async def test_get_card_detail_not_found(client: AsyncClient):
    r = await client.get("/api/cards/99999", headers=HEADERS)
    assert r.status_code == 404
