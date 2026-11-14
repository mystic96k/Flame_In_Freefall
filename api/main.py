"""Backend FastAPI de FIREFALL.

Arranque:
    uvicorn api.main:app --reload
Luego abre http://localhost:8000  (dashboard)  y  http://localhost:8000/docs  (documentación de la API)
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ai import analyst, llm_client, prompts
from ai.knowledge_base import load_catalog
from api.schemas import AskRequest, AskResponse, Prediction, Scenario
from config.settings import ROOT, RUNS_CSV
from ml import insights as ml_insights
from ml.predict import boundary_curves, load_classifier, predict_scenario

app = FastAPI(title="FIREFALL API", version="1.0",
              description="Datos, ML e IA sobre combustión en microgravedad (NASA Space Apps 2026).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@lru_cache(maxsize=1)
def runs() -> pd.DataFrame:
    if not RUNS_CSV.exists():
        raise HTTPException(503, "No hay datos procesados. Corre: python -m pipeline.run_pipeline")
    return pd.read_csv(RUNS_CSV)


@lru_cache(maxsize=1)
def cached_insights() -> list[dict]:
    return ml_insights.generate(runs())


def _ensure_model():
    try:
        load_classifier()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e


@app.get("/api/health")
def health():
    return {"status": "ok", "llm": llm_client.available(), "data": RUNS_CSV.exists()}


@app.get("/api/summary")
def summary():
    _ensure_model()
    df = runs()
    return {**ml_insights.summary(df),
            "materials": sorted(df["material"].dropna().astype(str).unique().tolist()),
            "investigations": sorted(df["investigation"].dropna().astype(str).unique().tolist())}


@app.get("/api/runs")
def list_runs(material: str | None = None, investigation: str | None = None, limit: int = Query(2000, le=10000)):
    df = runs()
    if material:
        df = df[df["material"] == material]
    if investigation:
        df = df[df["investigation"] == investigation]
    return json.loads(df.head(limit).to_json(orient="records"))  # NaN → null


@app.get("/api/boundary")
def boundary(gravity_g: float = 0.0, pressure_kpa: float = 101.3):
    _ensure_model()
    mats = sorted(runs()["material"].dropna().astype(str).unique())
    return boundary_curves(mats, gravity_g, pressure_kpa)


@app.post("/api/predict", response_model=Prediction)
def predict(s: Scenario):
    _ensure_model()
    return predict_scenario(s.material, s.o2_pct, s.flow_cm_s, s.gravity_g, s.pressure_kpa)


@app.get("/api/insights")
def get_insights():
    _ensure_model()
    return cached_insights()


@app.get("/api/catalog")
def catalog():
    return load_catalog()


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    _ensure_model()
    s = req.scenario
    pred = predict_scenario(s.material, s.o2_pct, s.flow_cm_s, s.gravity_g, s.pressure_kpa)
    return analyst.answer(req.question, s.model_dump(), pred, ml_insights.summary(runs()),
                          cached_insights(), [m.model_dump() for m in req.history])


@app.post("/api/report", response_model=AskResponse)
def report(s: Scenario):
    return ask(AskRequest(question=prompts.REPORT_REQUEST, scenario=s))


# El dashboard se sirve desde la misma app (un solo servicio para desplegar).
app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
