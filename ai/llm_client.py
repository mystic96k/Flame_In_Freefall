"""Cliente de modelo de lenguaje independiente del proveedor.

LLM_PROVIDER en .env:
  anthropic          → API de Claude (ANTHROPIC_API_KEY)
  openai_compatible  → Groq, OpenAI, Together, Ollama local... (OPENAI_BASE_URL + OPENAI_API_KEY)
  none               → sin IA: respuesta armada con el modelo de ML y la base de conocimiento

La llave vive SOLO en el backend; el navegador nunca la ve.

Si el proveedor retira el modelo configurado (Groq lo hace seguido), el cliente
consulta la lista de modelos disponibles y elige uno de reemplazo automáticamente.
"""
from __future__ import annotations

import httpx

from config import settings

# Preferencias de reemplazo para APIs compatibles con OpenAI (Groq primero).
FALLBACK_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
_resolved_model: str | None = None
last_error: str | None = None


class LLMUnavailable(RuntimeError):
    pass


def available() -> bool:
    if settings.LLM_PROVIDER == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if settings.LLM_PROVIDER == "openai_compatible":
        local = "localhost" in settings.OPENAI_BASE_URL or "127.0.0.1" in settings.OPENAI_BASE_URL
        return bool(settings.OPENAI_BASE_URL) and (local or bool(settings.OPENAI_API_KEY))
    return False


def _describe(r: httpx.Response) -> str:
    try:
        err = r.json().get("error", {})
        msg = err.get("message") if isinstance(err, dict) else str(err)
    except Exception:
        msg = r.text
    return f"HTTP {r.status_code}: {(msg or '')[:200]}"


def _anthropic(system: str, messages: list[dict], max_tokens: int) -> str:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": settings.ANTHROPIC_MODEL, "max_tokens": max_tokens, "system": system, "messages": messages},
        timeout=90,
    )
    if r.status_code >= 400:
        raise RuntimeError(_describe(r))
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"} if settings.OPENAI_API_KEY else {}


def _pick_available_model() -> str | None:
    """Pregunta al proveedor qué modelos tiene y elige el mejor de reemplazo."""
    r = httpx.get(f"{settings.OPENAI_BASE_URL.rstrip('/')}/models", headers=_headers(), timeout=20)
    if r.status_code >= 400:
        return None
    ids = [m.get("id") for m in r.json().get("data", []) if m.get("active", True)]
    for m in FALLBACK_MODELS:
        if m in ids:
            return m
    chat_like = [i for i in ids if i and not any(x in i for x in ("whisper", "guard", "tts", "embed", "orpheus"))]
    return chat_like[0] if chat_like else None


def _openai_compatible(system: str, messages: list[dict], max_tokens: int) -> str:
    global _resolved_model
    model = _resolved_model or settings.OPENAI_MODEL

    def call(model_id: str) -> httpx.Response:
        body = {"model": model_id, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, *messages]}
        if "gpt-oss" in model_id:
            body["reasoning_effort"] = "low"   # respuestas rápidas; menos tokens de razonamiento
        return httpx.post(f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                          headers=_headers(), json=body, timeout=90)

    r = call(model)
    if r.status_code in (400, 404) and "model" in r.text.lower():
        replacement = _pick_available_model()
        if replacement and replacement != model:
            _resolved_model = replacement
            r = call(replacement)
    if r.status_code >= 400:
        raise RuntimeError(_describe(r))
    msg = r.json()["choices"][0]["message"]
    return msg.get("content") or ""


def current_model() -> str | None:
    if settings.LLM_PROVIDER == "anthropic":
        return settings.ANTHROPIC_MODEL
    if settings.LLM_PROVIDER == "openai_compatible":
        return _resolved_model or settings.OPENAI_MODEL
    return None


def chat(system: str, messages: list[dict], max_tokens: int = 2000) -> str:
    """messages = [{"role": "user"|"assistant", "content": str}, ...] terminando en user."""
    global last_error
    if not available():
        raise LLMUnavailable("No hay proveedor de IA configurado.")
    try:
        text = (_anthropic if settings.LLM_PROVIDER == "anthropic" else _openai_compatible)(system, messages, max_tokens)
        last_error = None
        if not text.strip():
            raise RuntimeError("El modelo respondió vacío")
        return text
    except Exception as e:
        last_error = str(e)
        raise
