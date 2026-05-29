from __future__ import annotations

import httpx

from api.settings import settings
from llm.base import LLMBase

_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_DEFAULT_MODEL = "qwen/qwen3-8b:free"


class OpenRouterLLM(LLMBase):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.extract_model or _DEFAULT_MODEL
        self.api_key = settings.openrouter_api_key

    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "snap-vocab",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]
