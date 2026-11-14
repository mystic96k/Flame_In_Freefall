"""Convierte la tabla REAL de pruebas de BASS / BASS-II (tela algodón-fibra de vidrio SIBAL) en observaciones.

Fuente: Zhao, T'ien, Ferkul y Olson (2015), "Concurrent flame growth, spread and extinction over
composite fabric samples in low speed purely forced flow in microgravity", 9th U.S. National
Combustion Meeting. NTRS 20150008962, Apéndice. https://ntrs.nasa.gov/citations/20150008962
Condiciones: 1 atm, flujo forzado 1–55 cm/s, O2 16–21 % en volumen, microgravedad (ISS).

Cómo se interpreta cada fila:
  - Flujo "a->b": la llama se encendió con flujo a y luego se cambió el flujo a b durante la prueba.
      * Observación 1: (a, O2) → ardió.
      * Observación 2: (b, O2) → se apagó si dice "Quenched" o "Blow-off"; si no, siguió ardiendo.
  - "No ignition": se registra como no_ignition (el modelo NO la usa: no ignitar no es lo mismo que apagarse).
  - "Reused, did not ignite": muestra reutilizada; se excluye del modelo por ser poco confiable.

Uso:
    python -m pipeline.bass2_appendix      → data/raw/psi/bass2_observations.csv
"""
from __future__ import annotations

import pandas as pd

from config.settings import RAW_NTRS_DIR, RAW_PSI_DIR

RAW = RAW_NTRS_DIR / "bass2_appendix_raw.csv"
OUT = RAW_PSI_DIR / "bass2_observations.csv"
SOURCE = "NTRS 20150008962, Apéndice (Zhao, T'ien, Ferkul, Olson 2015)"
MATERIAL = "SIBAL (algodón/fibra de vidrio)"


def expand(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in raw.itertuples(index=False):
        comment = str(r.comments) if pd.notna(r.comments) else ""
        low = comment.lower()
        base = dict(investigation=r.campaign, material=MATERIAL, geometry=f"tela delgada, ancho {r.sample_width_cm} cm",
                    o2_pct=float(r.o2_pct), pressure_kpa=101.3, gravity_g=0.0)
        flows = [float(x) for x in str(r.flow_cm_s).split("->")]

        if "reused" in low and "did not ignite" in low:
            rows.append({**base, "run_id": r.test_no, "flow_cm_s": flows[0], "outcome": "excluded",
                         "notes": f"Excluida: {comment}"})
            continue
        if "no ignition" in low:
            rows.append({**base, "run_id": r.test_no, "flow_cm_s": flows[0], "outcome": "no_ignition",
                         "notes": comment})
            continue

        # La llama ardió con el flujo inicial.
        rows.append({**base, "run_id": f"{r.test_no}" + ("-a" if len(flows) > 1 else ""),
                     "flow_cm_s": flows[0], "outcome": "burn", "notes": comment})
        if len(flows) > 1:
            if "quench" in low:
                outcome = "extinct (quenching)"
            elif "blow-off" in low and "no blow-off" not in low:
                outcome = "extinct (blow-off)"
            else:
                outcome = "burn"
            rows.append({**base, "run_id": f"{r.test_no}-b", "flow_cm_s": flows[1], "outcome": outcome,
                         "notes": f"Flujo cambiado {flows[0]}→{flows[1]} cm/s. {comment}".strip()})
    out = pd.DataFrame(rows)
    out["source"] = SOURCE
    return out


def main() -> None:
    raw = pd.read_csv(RAW)
    obs = expand(raw)
    obs.to_csv(OUT, index=False)
    used = obs["outcome"].str.startswith(("burn", "extinct")).sum()
    print(f"✅ {len(raw)} pruebas reales → {len(obs)} observaciones ({used} utilizables por el modelo) → {OUT}")


if __name__ == "__main__":
    main()
