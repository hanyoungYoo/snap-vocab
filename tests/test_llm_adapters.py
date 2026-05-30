from __future__ import annotations

import httpx
import pytest
import respx

from llm.base import get_llm
from llm.ollama import OllamaLLM
from llm.openrouter import OpenRouterLLM

# ---------------------------------------------------------------------------
# OllamaLLM
# ---------------------------------------------------------------------------


@respx.mock
async def test_ollama_sends_correct_payload():
    model = "llama3:latest"
    route = respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "hello"}})
    )

    llm = OllamaLLM(model=model)
    result = await llm.complete("sys", "user input")

    assert result == "hello"
    assert route.called
    body = route.calls[0].request
    import json

    payload = json.loads(body.content)
    assert payload["model"] == model
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert payload["stream"] is False
    assert payload["think"] is False


@respx.mock
async def test_ollama_thinking_model_sets_think_true():
    route = respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "ok"}})
    )

    llm = OllamaLLM(model="qwen3:thinking")
    await llm.complete("sys", "user")

    import json

    payload = json.loads(route.calls[0].request.content)
    assert payload["think"] is True


@respx.mock
async def test_ollama_http_error_propagates():
    respx.post("http://localhost:11434/api/chat").mock(return_value=httpx.Response(503))

    llm = OllamaLLM(model="llama3:latest")
    with pytest.raises(httpx.HTTPStatusError):
        await llm.complete("sys", "user")


@respx.mock
async def test_ollama_custom_base_url(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "ollama_base_url", "http://myhost:11434")
    route = respx.post("http://myhost:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "custom"}})
    )

    llm = OllamaLLM(model="llama3:latest")
    result = await llm.complete("sys", "user")

    assert result == "custom"
    assert route.called


# ---------------------------------------------------------------------------
# OpenRouterLLM
# ---------------------------------------------------------------------------

_OR_URL = "https://openrouter.ai/api/v1/chat/completions"


@respx.mock
async def test_openrouter_sends_correct_payload(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "openrouter_api_key", "test-key")

    route = respx.post(_OR_URL).mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "world"}}]},
        )
    )

    llm = OpenRouterLLM(model="qwen/qwen3-8b:free")
    result = await llm.complete("sys", "user input", max_tokens=128)

    assert result == "world"
    assert route.called

    import json

    req = route.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-key"
    assert req.headers["X-Title"] == "snap-vocab"

    payload = json.loads(req.content)
    assert payload["model"] == "qwen/qwen3-8b:free"
    assert payload["max_tokens"] == 128
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"


@respx.mock
async def test_openrouter_http_error_propagates(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "openrouter_api_key", "k")
    respx.post(_OR_URL).mock(return_value=httpx.Response(429))

    llm = OpenRouterLLM(model="qwen/qwen3-8b:free")
    with pytest.raises(httpx.HTTPStatusError):
        await llm.complete("sys", "user")


# ---------------------------------------------------------------------------
# get_llm factory
# ---------------------------------------------------------------------------


def test_get_llm_unknown_provider_raises(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "llm_provider", "unknown")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm()


def test_get_llm_returns_ollama(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "llm_provider", "ollama")
    llm = get_llm()
    assert isinstance(llm, OllamaLLM)


def test_get_llm_returns_openrouter(monkeypatch):
    from api import settings as settings_mod

    monkeypatch.setattr(settings_mod.settings, "llm_provider", "openrouter")
    monkeypatch.setattr(settings_mod.settings, "openrouter_api_key", "k")
    llm = get_llm()
    assert isinstance(llm, OpenRouterLLM)
