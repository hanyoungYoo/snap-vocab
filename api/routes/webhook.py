from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.settings import settings
from notification.telegram import TelegramNotification

router = APIRouter(prefix="/api", tags=["webhook"])


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad secret token")

    update = await request.json()

    message = update.get("message") or update.get("callback_query", {}).get("message") or {}
    chat_id = str(message.get("chat", {}).get("id", ""))
    if not chat_id or chat_id != settings.telegram_chat_id:
        return {"ok": True}

    text = message.get("text", "").strip()
    notif = TelegramNotification()

    if text == "/start":
        await notif.send_text(
            "snap-vocab 봇 시작. 복습 알림은 매일 정해진 시간에 옵니다."
        )
    elif text == "/ping":
        await notif.send_text("pong")
    elif text.startswith("/"):
        await notif.send_text(f"알 수 없는 커맨드: {text}")

    return {"ok": True}
