"""Orquestador: junta todas las fuentes en data/processed/runs.csv.

Prioridad:
  1. Datos reales de PSI ya convertidos (data/processed/psi_runs.csv) o tablas en data/raw/psi/
  2. Si no hay reales y ALLOW_DEMO_DATA=true → dataset de demostración

Uso:
    python -m pipeline.run_pipeline           # automático
    python -m pipeline.run_pipeline --demo    # fuerza demostración
    python -m pipeline.run_pipeline --mix     # reales + demostración (útil para pruebas de UI)
"""
from __future__ import annotations

import argparse

import pandas as pd

from config.settings import ALLOW_DEMO_DATA, DEMO_CSV, RUNS_CSV
from pipeline import ingest_psi_tables, make_demo_data
from pipeline.schema import validate


def build(force_demo: bool = False, mix: bool = False) -> pd.DataFrame:
    frames = []
    if not force_demo:
        real = ingest_psi_tables.ingest_all()
        if not real.empty:
            frames.append(real)
            print(f"Datos reales: {len(real)} pruebas de {real['investigation'].nunique()} investigaciones")
    if force_demo or mix or (not frames and ALLOW_DEMO_DATA):
        if not DEMO_CSV.exists():
            make_demo_data.main()
        demo = pd.read_csv(DEMO_CSV)
        frames.append(demo)
        print(f"Datos de demostración: {len(demo)} pruebas (is_demo=True)")
    if not frames:
        raise SystemExit("No hay datos. Agrega tablas a data/raw/psi/ o activa ALLOW_DEMO_DATA.")
    df = pd.concat(frames, ignore_index=True)
    for w in validate(df):
        print("⚠️ ", w)
    df.to_csv(RUNS_CSV, index=False)
    print(f"✅ {len(df)} pruebas → {RUNS_CSV}")
    try:  # gases BASS-II, gotas FLEX, BASS-I, SAFFIRE-I (data/processed/extra.json)
        from pipeline import nasa_extra
        e = nasa_extra.build()
        print(f"✅ Datos extra: {e['gases']['n_tests']} pruebas de gases + {e['flex']['n_tests']} gotas FLEX")
    except Exception as exc:  # noqa: BLE001
        print("⚠️  No pude generar datos extra:", exc)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--mix", action="store_true")
    a = ap.parse_args()
    build(a.demo, a.mix)


if __name__ == "__main__":
    main()
