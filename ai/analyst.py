"""El "analista IA": junta RAG + ML + escenario y le pregunta al modelo de lenguaje.

Si no hay IA configurada, regresa una respuesta automática útil (para que el
demo nunca se quede en blanco frente a los jueces).
"""
from __future__ import annotations

import json

from ai import llm_client, prompts
from ai.knowledge_base import get_kb


def _format_sources(question: str) -> tuple[str, list[dict]]:
    hits = get_kb().search(question, k=4)
    refs = [{"id": c.id, "title": c.title, "url": c.source, "kind": c.kind, "score": round(s, 3)} for c, s in hits]
    text = "\n".join(f"[{c.id}] {c.text}\n(fuente: {c.source})" for c, _ in hits) or "(sin coincidencias)"
    return text, refs


def answer(question: str, scenario: dict, prediction: dict, summary: dict, insights: list[dict],
           history: list[dict] | None = None) -> dict:
    sources_text, refs = _format_sources(question + " " + scenario.get("material", ""))
    context = prompts.CONTEXT.format(
        sources=sources_text,
        model=json.dumps({"resumen": summary, "prediccion_escenario": prediction}, ensure_ascii=False),
        insights="\n".join(f"- {i['text']}" for i in insights),
        scenario=json.dumps(scenario, ensure_ascii=False),
    )
    history = [m for m in (history or []) if m.get("role") in {"user", "assistant"}][-6:]
    raw = [*history, {"role": "user", "content": f"{context}\n\n---\nPregunta: {question}"}]
    messages: list[dict] = []
    for m in raw:  # garantiza turnos alternados que empiezan en "user"
        if not messages and m["role"] != "user":
            continue
        if messages and messages[-1]["role"] == m["role"]:
            messages[-1] = m
        else:
            messages.append(m)

    try:
        text = llm_client.chat(prompts.SYSTEM, messages)
        mode = "llm"
    except llm_client.LLMUnavailable:
        text = _offline(question, scenario, prediction, insights, refs)
        mode = "offline"
    except Exception as e:  # error de red / llave inválida
        text = _offline(question, scenario, prediction, insights, refs) + f"\n\n_(IA no disponible: {type(e).__name__})_"
        mode = "offline"
    return {"answer": text, "sources": refs, "mode": mode}


def _offline(question, scenario, prediction, insights, refs) -> str:
    loc = prediction.get("limiting_o2_pct")
    lines = [
        "**Respuesta automática (sin modelo de lenguaje)**",
        f"- Escenario: {scenario.get('gravity_g', 0)} g, {scenario.get('o2_pct')}% O₂, "
        f"{scenario.get('flow_cm_s')} cm/s, {scenario.get('material')}.",
        f"- Probabilidad de combustión sostenida: **{prediction['risk_score']}/100**"
        + (f"; O₂ límite estimado {loc}%." if loc else "."),
    ]
    if prediction.get("extrapolating"):
        lines.append("- ⚠️ El modelo está extrapolando fuera del rango de los datos.")
    lines += [f"- {i['text']}" for i in insights[:2]]
    if refs:
        lines.append("- Fuentes relacionadas: " + ", ".join(f"[{r['id']}]" for r in refs[:3]))
    return "\n".join(lines)
