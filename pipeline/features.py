"""Ingeniería de variables con sentido físico.

Idea clave para explicar en el pitch: en microgravedad no hay convección
natural, así que el oxígeno sólo llega por el flujo forzado (ventilación).
En la Tierra, la flotación aporta un "flujo" extra. Combinamos ambos en un
FLUJO EFECTIVO, y el límite de inflamabilidad tiene forma de U frente a él:
  - flujo muy bajo  → la llama se ahoga (falta oxígeno)      → extinción por "quenching"
  - flujo intermedio → máxima inflamabilidad
  - flujo muy alto  → la llama se "sopla"                     → extinción por "blow-off"
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import BUOYANT_FLOW_1G

NUMERIC_FEATURES = ["o2_pct", "log_ueff", "log_ueff_sq", "pressure_kpa"]
CATEGORICAL_FEATURES = ["material"]


def effective_flow(flow_cm_s, gravity_g):
    flow = np.asarray(flow_cm_s, dtype=float)
    g = np.asarray(gravity_g, dtype=float)
    return np.sqrt(flow ** 2 + (BUOYANT_FLOW_1G * g) ** 2) + 0.3


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["u_eff"] = effective_flow(out["flow_cm_s"], out["gravity_g"])
    out["log_ueff"] = np.log(out["u_eff"])
    out["log_ueff_sq"] = out["log_ueff"] ** 2
    out["flow_regime"] = pd.cut(out["u_eff"], bins=[0, 2, 25, np.inf],
                                labels=["casi quieto", "ventilación de cabina", "flujo alto"])
    return out


def model_ready(df: pd.DataFrame) -> pd.DataFrame:
    """Filas utilizables para entrenar (sin huecos en variables clave y con resultado conocido)."""
    df = add_features(df)
    mask = df[["o2_pct", "flow_cm_s"]].notna().all(axis=1) & df["outcome"].isin(["burn", "extinct"])
    return df[mask].reset_index(drop=True)
