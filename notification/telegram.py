from __future__ import annotations

from typing import Any

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from api.settings import settings
from notification.base import NotificationBase


class TelegramNotification(NotificationBase):
    def __init__(self) -> None:
        if not settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
        if not settings.telegram_chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID not set")
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id

    async def send_question(self, question: dict[str, Any]) -> str:
        qtype = question["type"]
        text = question["question"]
        if qtype == "multiple_choice":
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(opt, callback_data=f"ans:{question['card_id']}:{opt}")]
                    for opt in question["options"]
                ]
            )
            msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"📝 *문제*\n{text}",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        else:
            msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"📝 *빈칸 채우기*\n{text}\n\n답을 입력하세요:",
                parse_mode="Markdown",
            )
        return str(msg.message_id)

    async def send_feedback(self, text: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=text)

    async def send_text(self, text: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=text)

    async def answer_callback_query(self, callback_query_id: str) -> None:
        """Telegram에게 callback_query 수신 확인 — 미응답 시 Telegram이 계속 재전송."""
        await self.bot.answer_callback_query(callback_query_id=callback_query_id)
