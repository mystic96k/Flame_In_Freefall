"""Entrena el clasificador "¿se sostiene la llama?" (burn = 1 / extinct = 0).

Compara 3 modelos con validación cruzada y se queda con el mejor, pero
prefiere la regresión logística si está casi empatada: es interpretable,
da fronteras suaves y extrapola mejor con pocos datos (las tablas reales
de PSI suelen tener decenas de pruebas, no miles).

Uso:
    python -m ml.train_classifier
Salidas:
    ml/artifacts/classifier.joblib   modelo + metadatos
    ml/artifacts/metrics.json        métricas, importancia de variables, comparación
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config.settings import MODELS_DIR, RUNS_CSV
from pipeline.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, model_ready

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])


def candidates() -> dict[str, Pipeline]:
    return {
        "logistic": Pipeline([("prep", preprocessor()),
                              ("clf", LogisticRegression(C=3.0, max_iter=2000))]),
        "random_forest": Pipeline([("prep", preprocessor()),
                                   ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                                                  random_state=0))]),
        "gradient_boosting": Pipeline([("prep", preprocessor()),
                                       ("clf", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.08,
                                                                              random_state=0))]),
    }


def train(df: pd.DataFrame | None = None) -> dict:
    df = model_ready(df if df is not None else pd.read_csv(RUNS_CSV))
    if len(df) < 10 or df["burned"].nunique() < 2:
        raise SystemExit(f"Muy pocos datos utilizables ({len(df)}) o un solo tipo de resultado.")
    X, y = df[FEATURES], df["burned"]
    n_splits = int(max(2, min(5, y.value_counts().min())))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=0)

    scores = {}
    for name, model in candidates().items():
        res = cross_validate(model, X, y, cv=cv, scoring=["accuracy", "roc_auc", "f1"])
        scores[name] = {k: round(float(np.mean(res[f"test_{k}"])), 4) for k in ["accuracy", "roc_auc", "f1"]}
        print(f"{name:<18} acc={scores[name]['accuracy']:.3f}  auc={scores[name]['roc_auc']:.3f}  f1={scores[name]['f1']:.3f}")

    best = max(scores, key=lambda k: scores[k]["roc_auc"])
    chosen = "logistic" if scores["logistic"]["roc_auc"] >= scores[best]["roc_auc"] - 0.02 else best
    model = candidates()[chosen].fit(X, y)

    imp = permutation_importance(model, X, y, n_repeats=10, random_state=0, scoring="roc_auc")
    importance = sorted(({"feature": f, "importance": round(float(m), 4)}
                         for f, m in zip(FEATURES, imp.importances_mean)),
                        key=lambda d: -d["importance"])

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_runs": int(len(df)),
        "n_burned": int(y.sum()),
        "uses_demo_data": bool(df["is_demo"].astype(str).str.lower().eq("true").any()),
        "investigations": sorted(df["investigation"].astype(str).unique().tolist()),
        "materials": sorted(df["material"].astype(str).unique().tolist()),
        "cv_folds": n_splits,
        "comparison": scores,
        "chosen_model": chosen,
        "chosen_scores": scores[chosen],
        "feature_importance": importance,
        "feature_ranges": {c: [float(df[c].min()), float(df[c].max())]
                           for c in ["o2_pct", "flow_cm_s", "pressure_kpa", "gravity_g"]},
    }
    joblib.dump({"model": model, "features": FEATURES, "metrics": metrics}, MODELS_DIR / "classifier.joblib")
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Modelo elegido: {chosen}  (guardado en {MODELS_DIR})")
    return metrics


if __name__ == "__main__":
    train()
