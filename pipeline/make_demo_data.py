"""Genera un dataset SINTÉTICO de demostración para desarrollar sin conexión.

⚠️ No son mediciones. Cada fila queda marcada con is_demo=True y el dashboard
lo muestra con una etiqueta. Úsalo para construir y probar; para el pitch,
cámbialo por datos reales (ver README).

Modelo ilustrativo: límite de O2 con forma de U frente al flujo efectivo,
más ruido. Los valores base por material son aproximados y sólo didácticos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import DEMO_CSV
from pipeline.features import effective_flow
from pipeline.schema import conform

MATERIAL_BASE = {  # O2 mínimo aproximado (%) en el flujo más favorable — ilustrativo
    "SIBAL (algodón/fibra de vidrio)": 15.4,
    "PMMA": 16.4,
    "Silicón": 19.2,
    "Nomex": 23.5,
}
U_STAR, CURVATURE = 9.0, 0.95


def limiting_o2(material: str, flow, gravity=0.0, pressure_kpa=101.3):
    lu = np.log(effective_flow(flow, gravity) / U_STAR)
    pressure_penalty = 0.04 * (101.3 - np.asarray(pressure_kpa))  # menos presión → un poco más difícil arder
    return MATERIAL_BASE[material] + CURVATURE * lu ** 2 + pressure_penalty


def make(n: int = 240, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mats = rng.choice(list(MATERIAL_BASE), n)
    flow = np.exp(rng.uniform(np.log(0.6), np.log(42), n))
    o2 = rng.uniform(13, 32, n)
    pressure = rng.choice([101.3, 70.3, 56.5], n, p=[0.6, 0.25, 0.15])  # 56.5 kPa ≈ atmósfera de exploración
    loc = np.array([limiting_o2(m, f, 0.0, p) for m, f, p in zip(mats, flow, pressure)])
    margin = o2 - loc + rng.normal(0, 0.9, n)
    burned = margin > 0
    spread = np.where(burned, 0.25 * margin + 0.05 * np.minimum(flow, 25) + np.abs(rng.normal(0, 0.1, n)), np.nan)
    df = pd.DataFrame({
        "run_id": [f"DEMO-{i + 1:03d}" for i in range(n)],
        "material": mats,
        "geometry": rng.choice(["placa delgada", "placa gruesa", "cilindro"], n),
        "flow_cm_s": flow.round(2),
        "o2_pct": o2.round(2),
        "pressure_kpa": pressure,
        "gravity_g": 0.0,
        "outcome": np.where(burned, "burn", np.where(flow < 3, "extinct (quenching)", "extinct (blow-off)")),
        "spread_rate_mm_s": np.round(spread, 3),
        "notes": "dato sintético de demostración",
    })
    return conform(df, investigation="DEMO", source="make_demo_data.py", is_demo=True)


def main() -> None:
    df = make()
    df.to_csv(DEMO_CSV, index=False)
    print(f"Dataset de demostración: {len(df)} filas → {DEMO_CSV}")


if __name__ == "__main__":
    main()
