from __future__ import annotations

import httpx

from api.settings import settings
from llm.base import LLMBase

_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaLLM(LLMBase):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.extract_model
        self.base_url = (settings.ollama_base_url or _DEFAULT_BASE_URL).rstrip("/")

    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        # /no_think suffix suppresses <think>…</think> blocks from Qwen3
        if self.model.endswith(":thinking"):
            payload["think"] = True
        else:
            payload["think"] = False

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["message"]["content"]
