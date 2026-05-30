from __future__ import annotations

from abc import ABC, abstractmethod

from api.settings import settings


class LLMBase(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, *, max_tokens: int = 2048) -> str: ...


def get_llm(provider: str | None = None, model: str | None = None) -> LLMBase:
    provider = provider or settings.llm_provider
    if not provider:
        raise RuntimeError("LLM_PROVIDER is not set in .env")

    if provider == "claude":
        from llm.claude import ClaudeLLM

        return ClaudeLLM(model)
    if provider == "openai":
        raise NotImplementedError("openai provider not implemented yet")
    if provider == "gemini":
        raise NotImplementedError("gemini provider not implemented yet")
    if provider == "ollama":
        from llm.ollama import OllamaLLM

        return OllamaLLM(model)
    if provider == "openrouter":
        from llm.openrouter import OpenRouterLLM

        return OpenRouterLLM(model)
    raise ValueError(f"Unknown LLM provider: {provider}")
