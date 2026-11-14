"""Funciones de inferencia que usa la API: probabilidad, O2 límite y fronteras."""
from __future__ import annotations

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from config.settings import MODELS_DIR
from pipeline.features import add_features


@lru_cache(maxsize=1)
def load_classifier() -> dict:
    path = MODELS_DIR / "classifier.joblib"
    if not path.exists():
        raise FileNotFoundError("No hay modelo entrenado. Corre: python -m ml.train_classifier")
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_regressor() -> dict | None:
    path = MODELS_DIR / "spread_regressor.joblib"
    return joblib.load(path) if path.exists() else None


def reload_models() -> None:
    load_classifier.cache_clear()
    load_regressor.cache_clear()


def _frame(material, o2_pct, flow_cm_s, gravity_g=0.0, pressure_kpa=101.3) -> pd.DataFrame:
    n = max(np.size(o2_pct), np.size(flow_cm_s))
    df = pd.DataFrame({
        "material": np.broadcast_to(np.asarray(material, dtype=object), n),
        "o2_pct": np.broadcast_to(o2_pct, n).astype(float),
        "flow_cm_s": np.broadcast_to(flow_cm_s, n).astype(float),
        "gravity_g": np.broadcast_to(gravity_g, n).astype(float),
        "pressure_kpa": np.broadcast_to(pressure_kpa, n).astype(float),
    })
    return add_features(df)


def burn_probability(material, o2_pct, flow_cm_s, gravity_g=0.0, pressure_kpa=101.3) -> np.ndarray:
    bundle = load_classifier()
    X = _frame(material, o2_pct, flow_cm_s, gravity_g, pressure_kpa)[bundle["features"]]
    return bundle["model"].predict_proba(X)[:, 1]


def limiting_o2(material, flow_cm_s, gravity_g=0.0, pressure_kpa=101.3,
                lo: float = 8.0, hi: float = 60.0) -> float | None:
    """O2 (%) donde la probabilidad cruza 50%, por búsqueda binaria."""
    p = lambda o2: float(burn_probability(material, o2, flow_cm_s, gravity_g, pressure_kpa)[0])
    if p(hi) < 0.5:
        return None          # no arde ni con mucho oxígeno (dentro del rango del modelo)
    if p(lo) >= 0.5:
        return lo
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if p(mid) >= 0.5 else (mid, hi)
    return round((lo + hi) / 2, 2)


def predict_scenario(material: str, o2_pct: float, flow_cm_s: float,
                     gravity_g: float = 0.0, pressure_kpa: float = 101.3) -> dict:
    prob = float(burn_probability(material, o2_pct, flow_cm_s, gravity_g, pressure_kpa)[0])
    loc = limiting_o2(material, flow_cm_s, gravity_g, pressure_kpa)
    spread = None
    reg = load_regressor()
    if reg and prob >= 0.5:
        X = _frame(material, o2_pct, flow_cm_s, gravity_g, pressure_kpa)[reg["features"]]
        spread = round(float(reg["model"].predict(X)[0]), 3)
    ranges = load_classifier()["metrics"]["feature_ranges"]
    extrapolating = (not ranges["gravity_g"][0] <= gravity_g <= ranges["gravity_g"][1]
                     or not ranges["flow_cm_s"][0] <= flow_cm_s <= ranges["flow_cm_s"][1])
    return {
        "burn_probability": round(prob, 4),
        "risk_score": int(round(prob * 100)),
        "limiting_o2_pct": loc,
        "margin_pct": None if loc is None else round(o2_pct - loc, 2),
        "predicted_spread_mm_s": spread,
        "extrapolating": bool(extrapolating),
        "state": "burning" if prob >= 0.5 else "extinguished",
    }


def boundary_curves(materials: list[str], gravity_g: float = 0.0, pressure_kpa: float = 101.3,
                    n: int = 40) -> dict[str, list[dict]]:
    """Bisección vectorizada: todos los flujos a la vez (rápido para la API)."""
    flows = np.exp(np.linspace(np.log(0.6), np.log(42), n))
    curves = {}
    for m in materials:
        lo, hi = np.full(n, 8.0), np.full(n, 60.0)
        burns_at_hi = burn_probability(m, hi, flows, gravity_g, pressure_kpa) >= 0.5
        for _ in range(25):
            mid = (lo + hi) / 2
            ok = burn_probability(m, mid, flows, gravity_g, pressure_kpa) >= 0.5
            hi = np.where(ok, mid, hi)
            lo = np.where(ok, lo, mid)
        curves[m] = [{"flow_cm_s": round(float(f), 3), "o2_pct": round(float((a + b) / 2), 2)}
                     for f, a, b, valid in zip(flows, lo, hi, burns_at_hi) if valid]
    return curves
