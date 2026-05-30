from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.settings import settings
from bot.handlers.feedback import handle_choice, handle_text_answer
from notification.telegram import TelegramNotification

logger = logging.getLogger(__name__)

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
        callback_query_id = callback_query.get("id")
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))

        # answerCallbackQuery — Telegram 재시도 방지 (인증 무관하게 항상 응답)
        notif = TelegramNotification()
        await notif.answer_callback_query(callback_query_id)

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
                    logger.warning(
                        "callback_query: invalid card_id %r in data=%r", card_id_str, data
                    )
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
        await notif.send_text("snap-vocab 봇 시작. 복습 알림은 매일 정해진 시간에 옵니다.")
    elif text == "/ping":
        await notif.send_text("pong")
    elif text.startswith("/"):
        await notif.send_text(f"알 수 없는 커맨드: {text}")
    else:
        reply_to = message.get("reply_to_message", {}).get("message_id")
        await handle_text_answer(str(reply_to) if reply_to else None, text)

    return {"ok": True}
