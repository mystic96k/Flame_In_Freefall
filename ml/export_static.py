"""Exporta FIREFALL a una versión 100% estática (sin servidor) para Hugging Face Static o GitHub Pages.

Python sigue haciendo todo el trabajo pesado AQUÍ (limpieza, entrenamiento, fronteras,
hallazgos); el navegador sólo evalúa una regresión logística con los coeficientes exportados.

Limitaciones del modo estático:
  - El chat responde con la base de conocimiento (FAQ + catálogo) y el modelo de ML.
    Para IA real, despliega el backend en Render y pon su URL en docs/js/config.js
    (la llave de Anthropic vive en Render, nunca en la página pública).
  - Sin regresor de velocidad de propagación.

Uso:
    python -m pipeline.run_pipeline && python -m ml.train_classifier
    python -m ml.export_static
Salida:
    docs/   ← GitHub Pages la publica sola; o sube su contenido a un Space Static de Hugging Face
"""
from __future__ import annotations

import json
import shutil

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ai.knowledge_base import load_catalog, load_faq
from config.settings import BUOYANT_FLOW_1G, ROOT, RUNS_CSV
from ml import insights as ml_insights
from ml.predict import boundary_curves
from ml.train_classifier import FEATURES, preprocessor
from pipeline import nasa_extra
from pipeline.features import NUMERIC_FEATURES, model_ready

DIST = ROOT / "docs"   # GitHub Pages publica esta carpeta (Settings → Pages → main /docs)

SPACE_README = """---
title: FIREFALL
emoji: 🔥
colorFrom: yellow
colorTo: blue
sdk: static
app_file: index.html
pinned: false
short_description: Seguridad contra incendios en microgravedad con IA
---

# FIREFALL (versión estática)

Panel para el reto "Flame in Freefall" de NASA Space Apps 2026.
Código completo: ver el repositorio de GitHub del proyecto.
"""


def logistic_for_browser(df: pd.DataFrame) -> dict:
    """Entrena una regresión logística y la deja en números que JavaScript puede evaluar."""
    data = model_ready(df)
    model = Pipeline([("prep", preprocessor()), ("clf", LogisticRegression(C=3.0, max_iter=2000))])
    model.fit(data[FEATURES], data["burned"])
    prep = model.named_steps["prep"]
    scaler = prep.named_transformers_["num"]
    encoder = prep.named_transformers_["cat"]
    clf = model.named_steps["clf"]
    return {
        "type": "logistic",
        "numeric_features": NUMERIC_FEATURES,
        "mean": scaler.mean_.round(8).tolist(),
        "scale": scaler.scale_.round(8).tolist(),
        "categories": [str(c) for c in encoder.categories_[0]],
        "coef": clf.coef_[0].round(8).tolist(),
        "intercept": float(np.round(clf.intercept_[0], 8)),
        "buoyant_flow_1g": BUOYANT_FLOW_1G,
        "feature_ranges": {c: [float(df[c].min()), float(df[c].max())]
                           for c in ["flow_cm_s", "gravity_g", "pressure_kpa", "o2_pct"]},
    }


def _bust_cache(dist) -> None:
    """Pone ?v=<huella> en cada import y en index.html, para que el navegador no use archivos viejos."""
    import hashlib
    import re
    files = sorted(p for p in dist.rglob("*") if p.is_file() and p.suffix in {".js", ".css", ".html"})
    version = hashlib.sha1(b"".join(p.read_bytes() for p in files)).hexdigest()[:8]
    for js in (dist / "js").glob("*.js"):
        txt = js.read_text(encoding="utf-8")
        txt = re.sub(r'(from\s+"\./[\w-]+\.js)(?:\?v=\w+)?"', rf'\1?v={version}"', txt)
        txt = re.sub(r'(import\("\./[\w-]+\.js)(?:\?v=\w+)?"', rf'\1?v={version}"', txt)
        js.write_text(txt, encoding="utf-8")
    html = dist / "index.html"
    txt = html.read_text(encoding="utf-8")
    txt = re.sub(r'((?:css/styles\.css|js/main\.js|js/config\.js))(?:\?v=\w+)?"', rf'\1?v={version}"', txt)
    html.write_text(txt, encoding="utf-8")


def main() -> None:
    df = pd.read_csv(RUNS_CSV)
    materials = sorted(df["material"].dropna().astype(str).unique())
    summary = {**ml_insights.summary(df), "materials": materials,
               "investigations": sorted(df["investigation"].dropna().astype(str).unique())}
    bundle = {
        "mode": "static",
        "summary": summary,
        "runs": json.loads(df.to_json(orient="records")),
        "boundary": boundary_curves(materials),
        "insights": ml_insights.generate(df),
        "catalog": load_catalog(),
        "faq": load_faq(),
        "model": logistic_for_browser(df),
        "extra": nasa_extra.load_extra() or nasa_extra.build(),
    }

    cfg = DIST / "js" / "config.js"
    saved_cfg = cfg.read_text(encoding="utf-8") if cfg.exists() else None  # conserva la URL del backend
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "frontend", DIST)
    if saved_cfg is not None:
        cfg.write_text(saved_cfg, encoding="utf-8")
    _bust_cache(DIST)
    (DIST / "data").mkdir(exist_ok=True)
    (DIST / "data" / "static.json").write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    (DIST / "README.md").write_text(SPACE_README, encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: servir tal cual
    size_kb = (DIST / "data" / "static.json").stat().st_size / 1024
    print(f"✅ Versión estática lista en {DIST}  (datos: {size_kb:.0f} KB)")
    print("   Haz commit y push: GitHub Pages la actualiza sola en ~1 minuto.")


if __name__ == "__main__":
    main()
