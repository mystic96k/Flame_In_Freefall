"""Cliente de modelo de lenguaje independiente del proveedor.

LLM_PROVIDER en .env:
  anthropic          → API de Claude (ANTHROPIC_API_KEY)
  openai_compatible  → OpenAI, Groq, Together, Ollama local... (OPENAI_BASE_URL + OPENAI_API_KEY)
  none               → sin IA: respuesta armada con el modelo de ML y la base de conocimiento

La llave vive SOLO en el backend; el navegador nunca la ve.
"""
from __future__ import annotations

import httpx

from config import settings


class LLMUnavailable(RuntimeError):
    pass


def available() -> bool:
    if settings.LLM_PROVIDER == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if settings.LLM_PROVIDER == "openai_compatible":
        local = "localhost" in settings.OPENAI_BASE_URL or "127.0.0.1" in settings.OPENAI_BASE_URL
        return bool(settings.OPENAI_BASE_URL) and (local or bool(settings.OPENAI_API_KEY))
    return False


def chat(system: str, messages: list[dict], max_tokens: int = 900) -> str:
    """messages = [{"role": "user"|"assistant", "content": str}, ...] terminando en user."""
    if not available():
        raise LLMUnavailable("No hay proveedor de IA configurado.")
    if settings.LLM_PROVIDER == "anthropic":
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": settings.ANTHROPIC_MODEL, "max_tokens": max_tokens,
                  "system": system, "messages": messages},
            timeout=60,
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")

    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"} if settings.OPENAI_API_KEY else {}
    r = httpx.post(
        f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        headers=headers,
        json={"model": settings.OPENAI_MODEL, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, *messages]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
