from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.settings import settings
from bot.handlers.feedback import handle_choice, handle_text_answer
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

    callback_query = update.get("callback_query")
    if callback_query:
        chat_id = str(
            callback_query.get("message", {}).get("chat", {}).get("id", "")
        )
        if not chat_id or chat_id != settings.telegram_chat_id:
            return {"ok": True}
        data = callback_query.get("data", "")
        if data.startswith("ans:"):
            parts = data.split(":", 2)
            if len(parts) == 3:
                _, card_id_str, choice = parts
                try:
                    await handle_choice(int(card_id_str), choice)
                except ValueError:
                    pass
        return {"ok": True}

    message = update.get("message") or {}
    chat_id = str(message.get("chat", {}).get("id", ""))
    if not chat_id or chat_id != settings.telegram_chat_id:
        return {"ok": True}

    text = (message.get("text") or "").strip()
    if not text:
        return {"ok": True}

    notif = TelegramNotification()

    if text == "/start":
        await notif.send_text(
            "snap-vocab 봇 시작. 복습 알림은 매일 정해진 시간에 옵니다."
        )
    elif text == "/ping":
        await notif.send_text("pong")
    elif text.startswith("/"):
        await notif.send_text(f"알 수 없는 커맨드: {text}")
    else:
        reply_to = message.get("reply_to_message", {}).get("message_id")
        await handle_text_answer(str(reply_to) if reply_to else None, text)

    return {"ok": True}
