"""Regresor de velocidad de propagación de la llama (mm/s) para las pruebas que sí ardieron.

Sólo se entrena si hay suficientes pruebas con spread_rate_mm_s.

Uso:
    python -m ml.train_regressor
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline

from config.settings import MODELS_DIR, RUNS_CSV
from ml.train_classifier import FEATURES, preprocessor
from pipeline.features import model_ready

MIN_ROWS = 12


def train(df: pd.DataFrame | None = None) -> dict | None:
    df = model_ready(df if df is not None else pd.read_csv(RUNS_CSV))
    df = df[(df["burned"] == 1) & df["spread_rate_mm_s"].notna()]
    if len(df) < MIN_ROWS:
        print(f"Sólo {len(df)} pruebas con velocidad de propagación; se omite el regresor (mínimo {MIN_ROWS}).")
        return None
    model = Pipeline([("prep", preprocessor()),
                      ("reg", RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=0))])
    cv = KFold(n_splits=min(5, len(df) // 3), shuffle=True, random_state=0)
    mae = -cross_val_score(model, df[FEATURES], df["spread_rate_mm_s"], cv=cv,
                           scoring="neg_mean_absolute_error")
    model.fit(df[FEATURES], df["spread_rate_mm_s"])
    metrics = {"n_runs": int(len(df)), "mae_mm_s": round(float(np.mean(mae)), 4),
               "target_mean_mm_s": round(float(df["spread_rate_mm_s"].mean()), 4)}
    joblib.dump({"model": model, "features": FEATURES, "metrics": metrics}, MODELS_DIR / "spread_regressor.joblib")
    (MODELS_DIR / "spread_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"✅ Regresor de propagación: MAE={metrics['mae_mm_s']} mm/s sobre {len(df)} pruebas")
    return metrics


if __name__ == "__main__":
    train()
