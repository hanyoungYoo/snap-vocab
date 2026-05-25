from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.settings import settings


class FakeTelegramNotification:
    sent: list[str] = []

    def __init__(self) -> None:
        pass

    async def send_text(self, text: str) -> None:
        FakeTelegramNotification.sent.append(text)

    async def send_feedback(self, text: str) -> None:
        FakeTelegramNotification.sent.append(text)


@pytest.fixture
def webhook_env(monkeypatch):
    monkeypatch.setattr(settings, "telegram_chat_id", "111", raising=False)
    monkeypatch.setattr(settings, "telegram_webhook_secret", "s3cret", raising=False)
    import api.routes.webhook as webhook_mod

    monkeypatch.setattr(webhook_mod, "TelegramNotification", FakeTelegramNotification)
    FakeTelegramNotification.sent = []
    yield


@pytest.fixture
async def webhook_client():
    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


def _msg(chat_id: int, text: str) -> dict:
    return {"message": {"chat": {"id": chat_id}, "text": text}}


@pytest.mark.asyncio
async def test_bad_secret_returns_401(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(111, "/ping"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert r.status_code == 401
    assert FakeTelegramNotification.sent == []


@pytest.mark.asyncio
async def test_missing_secret_header_returns_401(webhook_env, webhook_client):
    r = await webhook_client.post("/api/webhook/telegram", json=_msg(111, "/ping"))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_other_chat_id_is_ignored(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(999, "/ping"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert FakeTelegramNotification.sent == []


@pytest.mark.asyncio
async def test_ping_returns_pong(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(111, "/ping"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )
    assert r.status_code == 200
    assert FakeTelegramNotification.sent == ["pong"]


@pytest.mark.asyncio
async def test_start_sends_intro(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(111, "/start"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )
    assert r.status_code == 200
    assert len(FakeTelegramNotification.sent) == 1
    assert "snap-vocab" in FakeTelegramNotification.sent[0]


@pytest.mark.asyncio
async def test_unknown_command_replies(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(111, "/whatever"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )
    assert r.status_code == 200
    assert FakeTelegramNotification.sent == ["알 수 없는 커맨드: /whatever"]


@pytest.mark.asyncio
async def test_plain_text_is_ignored(webhook_env, webhook_client):
    r = await webhook_client.post(
        "/api/webhook/telegram",
        json=_msg(111, "hello"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
    )
    assert r.status_code == 200
    assert FakeTelegramNotification.sent == []
