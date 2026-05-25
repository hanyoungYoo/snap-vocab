from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from api.settings import settings


class NotificationBase(ABC):
    @abstractmethod
    async def send_question(self, question: dict[str, Any]) -> str:
        """Send a review question. Returns the provider message id."""

    @abstractmethod
    async def send_feedback(self, text: str) -> None: ...

    @abstractmethod
    async def send_text(self, text: str) -> None: ...


def get_notification(provider: str | None = None) -> NotificationBase:
    provider = provider or settings.notification_provider
    if provider == "telegram":
        from notification.telegram import TelegramNotification

        return TelegramNotification()
    if provider in {"slack", "discord"}:
        raise NotImplementedError(f"{provider} provider not implemented yet")
    raise ValueError(f"Unknown notification provider: {provider}")
