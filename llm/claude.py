from __future__ import annotations

import anthropic

from api.settings import settings
from llm.base import LLMBase


class ClaudeLLM(LLMBase):
    def __init__(self, model: str | None = None) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.llm_api_key or None)
        self.model = model or settings.extract_model

    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str:
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        for block in resp.content:
            if block.type == "text":
                return block.text
        return ""
