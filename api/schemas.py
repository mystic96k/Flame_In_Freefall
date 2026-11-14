"""Modelos Pydantic: contratos de entrada/salida de la API (también generan la doc en /docs)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    material: str = Field("PMMA", examples=["PMMA"])
    o2_pct: float = Field(21.0, ge=5, le=100, description="Oxígeno en volumen (%)")
    flow_cm_s: float = Field(10.0, ge=0, le=200, description="Flujo de aire forzado (cm/s)")
    gravity_g: float = Field(0.0, ge=0, le=1.5, description="0 = ISS, 0.165 = Luna, 0.38 = Marte, 1 = Tierra")
    pressure_kpa: float = Field(101.3, ge=20, le=120)


class Prediction(BaseModel):
    burn_probability: float
    risk_score: int
    limiting_o2_pct: float | None
    margin_pct: float | None
    predicted_spread_mm_s: float | None
    extrapolating: bool
    state: str


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    scenario: Scenario = Scenario()
    history: list[ChatMessage] = []
    lang: str = Field("es", pattern="^(es|en)$", description="Idioma de la respuesta: es | en")


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    mode: str  # "llm" | "offline"
