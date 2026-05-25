import pytest
from httpx import AsyncClient

API_KEY = "test-secret"
HEADERS = {"X-API-Key": API_KEY}


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_save_card(client: AsyncClient):
    r = await client.post("/api/cards", json={"text": "beat around the bush"}, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] == ["beat around the bush"]
    assert data["duplicates"] == []


@pytest.mark.asyncio
async def test_duplicate_card(client: AsyncClient):
    payload = {"text": "spill the beans"}
    await client.post("/api/cards", json=payload, headers=HEADERS)

    r = await client.post("/api/cards", json=payload, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] == []
    assert data["duplicates"] == ["spill the beans"]


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
async def test_webhook_not_implemented(client: AsyncClient):
    r = await client.post("/api/webhook/telegram", headers=HEADERS)
    assert r.status_code == 501


@pytest.mark.asyncio
async def test_dashboard_not_implemented(client: AsyncClient):
    r = await client.get("/dashboard")
    assert r.status_code == 501
