"""Esquema estándar de una prueba de combustión y su validación.

Todas las fuentes (PSI, PDFs de NTRS, datos de demostración) se convierten a
estas columnas para que el modelo de ML y el dashboard no dependan del
formato original de cada experimento.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

COLUMNS = [
    "run_id",            # identificador de la prueba
    "investigation",     # BASS, BASS-II, FLEX, SoFIE, Saffire, DEMO...
    "material",          # nombre normalizado del material/combustible
    "geometry",          # placa delgada, esfera, cilindro, gota...
    "flow_cm_s",         # velocidad del flujo de aire forzado (cm/s)
    "o2_pct",            # oxígeno en volumen (%)
    "pressure_kpa",      # presión total (kPa)
    "gravity_g",         # nivel de gravedad (0 = microgravedad)
    "outcome",           # burn | extinct | no_ignition | unknown
    "burned",            # 1 si hubo combustión sostenida, 0 si no
    "spread_rate_mm_s",  # velocidad de propagación de la llama (si existe)
    "source",            # archivo o URL de origen
    "is_demo",           # True si es dato sintético de demostración
    "notes",
]

NUMERIC = ["flow_cm_s", "o2_pct", "pressure_kpa", "gravity_g", "spread_rate_mm_s"]

# Palabras clave para normalizar el resultado de cada prueba.
_OUTCOME_RULES = [
    (r"no[\s_-]*ign|did not ignite|not ignited|failed to ignite", "no_ignition"),
    (r"quench|extin|blow[\s-]*off|self[\s-]*extin|went out|\bout\b", "extinct"),
    (r"burn|ignit|sustain|spread|consumed|steady", "burn"),
]

_MATERIAL_ALIASES = {
    "pmma": "PMMA", "acrylic": "PMMA", "acrílico": "PMMA", "plexiglas": "PMMA",
    "sibal": "SIBAL (algodón/fibra de vidrio)", "cotton-fiberglass": "SIBAL (algodón/fibra de vidrio)",
    "cotton/fiberglass": "SIBAL (algodón/fibra de vidrio)", "cotton fiberglass": "SIBAL (algodón/fibra de vidrio)",
    "nomex": "Nomex", "silicone": "Silicón", "silicón": "Silicón", "cotton": "Algodón",
    "delrin": "Delrin", "polyoxymethylene": "Delrin", "pom": "Delrin",
    "heptane": "n-heptano", "n-heptane": "n-heptano", "methanol": "Metanol",
    "ethanol": "Etanol", "decane": "n-decano",
}


def normalize_outcome(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "unknown"
    if isinstance(value, (int, np.integer, bool, np.bool_)):
        return "burn" if int(value) == 1 else "extinct"
    text = str(value).strip().lower()
    if text in {"1", "yes", "y", "si", "sí", "true"}:
        return "burn"
    if text in {"0", "no", "n", "false"}:
        return "extinct"
    for pattern, label in _OUTCOME_RULES:
        if re.search(pattern, text):
            return label
    return "unknown"


def normalize_material(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Desconocido"
    text = str(value).strip()
    low = text.lower()
    for key, name in _MATERIAL_ALIASES.items():
        if key in low:
            return name
    return text


def to_number(series: pd.Series) -> pd.Series:
    """Convierte texto como '21 %', '10.5 cm/s' o '1,013' a número."""
    if series.dtype.kind in "if":
        return series.astype(float)
    cleaned = (series.astype(str)
               .str.replace(",", "", regex=False)
               .str.extract(r"(-?\d+(?:\.\d+)?)")[0])
    return pd.to_numeric(cleaned, errors="coerce")


def conform(df: pd.DataFrame, *, investigation: str, source: str,
            is_demo: bool = False, defaults: dict | None = None) -> pd.DataFrame:
    """Deja un DataFrame con exactamente las COLUMNS, tipos correctos y valores normalizados."""
    out = df.copy()
    defaults = defaults or {}
    for col in COLUMNS:
        if col not in out.columns:
            out[col] = defaults.get(col, np.nan)
    for col in NUMERIC:
        out[col] = to_number(out[col])
        if col in defaults:
            out[col] = out[col].fillna(defaults[col])

    out["investigation"] = out["investigation"].fillna(investigation).replace("", investigation)
    out["material"] = out["material"].map(normalize_material)
    out["outcome"] = out["outcome"].map(normalize_outcome)
    out["burned"] = (out["outcome"] == "burn").astype(int)
    out["pressure_kpa"] = out["pressure_kpa"].fillna(101.3)
    out["gravity_g"] = out["gravity_g"].fillna(0.0)
    out["source"] = out["source"].where(out["source"].notna() & (out["source"].astype(str) != ""), source)
    out["is_demo"] = bool(is_demo)
    if out["run_id"].isna().all():
        out["run_id"] = [f"{investigation}-{i + 1:03d}" for i in range(len(out))]
    out["run_id"] = out["run_id"].astype(str)
    return out[COLUMNS]


def validate(df: pd.DataFrame) -> list[str]:
    """Regresa una lista de advertencias (vacía si todo está bien)."""
    warnings: list[str] = []
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        warnings.append(f"Faltan columnas: {missing}")
        return warnings
    if df["o2_pct"].isna().mean() > 0.2:
        warnings.append("Más del 20% de las pruebas no tiene O2 → el modelo las descartará.")
    if df["flow_cm_s"].isna().mean() > 0.2:
        warnings.append("Más del 20% de las pruebas no tiene flujo → el modelo las descartará.")
    bad_o2 = df[(df["o2_pct"] < 5) | (df["o2_pct"] > 100)]
    if len(bad_o2):
        warnings.append(f"{len(bad_o2)} pruebas con O2 fuera de rango (5–100%). ¿Viene en fracción (0.21)?")
    if (df["outcome"] == "unknown").mean() > 0.1:
        warnings.append("Más del 10% de resultados no se pudo interpretar → revisa la columna outcome.")
    if df.duplicated(subset=["investigation", "run_id"]).any():
        warnings.append("Hay run_id duplicados dentro de una misma investigación.")
    return warnings
