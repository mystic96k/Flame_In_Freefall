"""Lee las Experiment Tables descargadas de PSI (CSV/XLSX) y las convierte al esquema estándar.

Como cada investigación nombra sus columnas distinto, hay dos capas de mapeo:
  1. Automático: busca palabras clave en el encabezado (oxygen, O2, flow, velocity...).
  2. Manual: lo que escribas en config/column_maps.yaml gana sobre lo automático.

Uso:
    python -m pipeline.ingest_psi_tables --inspect   # muestra columnas y el mapeo sugerido
    python -m pipeline.ingest_psi_tables             # convierte todo y guarda data/processed/psi_runs.csv
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import yaml

from config.settings import COLUMN_MAP_YAML, PROCESSED_DIR, RAW_PSI_DIR
from pipeline.schema import conform, validate

# Orden importa: la primera regla que coincide gana.
AUTO_RULES: list[tuple[str, str]] = [
    (r"^(test|run|point)(\s*(#|no\.?|num(ber)?|id))?\s*$|^id$", "run_id"),
    (r"spread\s*rate|flame\s*speed|v_?f\b", "spread_rate_mm_s"),
    (r"\bo2\b|oxygen|x_?o2|o₂", "o2_pct"),
    (r"flow|velocity|air\s*speed|\bu\b", "flow_cm_s"),
    (r"pressure|\bkpa\b|\bpsia?\b|\batm\b", "pressure_kpa"),
    (r"material|fuel|sample\s*type|sample$", "material"),
    (r"geometry|shape|thickness|config", "geometry"),
    (r"result|outcome|extinct|status|observ", "outcome"),
    (r"gravity|\bg[- ]?level\b", "gravity_g"),
    (r"comment|note|remark", "notes"),
]


def auto_map(columns: list[str]) -> dict[str, str]:
    from pipeline.schema import COLUMNS
    # 1) columnas que ya vienen con el nombre estándar
    mapping: dict[str, str] = {c: c for c in columns if c in COLUMNS}
    used: set[str] = set(mapping.values())
    for col in columns:
        if col in mapping:
            continue
        low = str(col).strip().lower()
        for pattern, target in AUTO_RULES:
            if target not in used and re.search(pattern, low):
                mapping[col] = target
                used.add(target)
                break
    return mapping


def unit_factor(col_name: str, target: str) -> float:
    """Detecta unidades comunes en el nombre de la columna."""
    low = col_name.lower()
    if target == "pressure_kpa":
        if "psi" in low:
            return 6.89476
        if "atm" in low:
            return 101.325
        if "bar" in low:
            return 100.0
    if target == "flow_cm_s" and ("mm/s" in low):
        return 0.1
    if target == "flow_cm_s" and ("m/s" in low and "cm/s" not in low and "mm/s" not in low):
        return 100.0
    if target == "spread_rate_mm_s" and "cm/s" in low:
        return 10.0
    return 1.0


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path, sep=None, engine="python")  # detecta , ; o tab


def load_config() -> dict:
    if COLUMN_MAP_YAML.exists():
        return yaml.safe_load(COLUMN_MAP_YAML.read_text(encoding="utf-8")) or {}
    return {}


def convert(path: Path, cfg: dict, verbose: bool = False) -> pd.DataFrame:
    raw = read_table(path)
    raw.columns = [str(c).strip() for c in raw.columns]
    file_cfg = (cfg.get("files") or {}).get(path.stem, {})
    manual = {k: v for k, v in (file_cfg.get("columns") or {}).items() if k in raw.columns}
    mapping = {**auto_map(list(raw.columns)), **manual}
    # quitar duplicados de destino (gana el manual)
    seen, final = set(), {}
    for src, dst in sorted(mapping.items(), key=lambda kv: kv[0] not in manual):
        if dst not in seen:
            final[src] = dst
            seen.add(dst)

    if verbose:
        print(f"\n📄 {path.name}  ({len(raw)} filas)")
        for c in raw.columns:
            tag = "manual" if c in manual else ("auto" if c in final else "—")
            print(f"   {c:<40} → {final.get(c, '(ignorada)'):<18} [{tag}]")

    df = raw[list(final)].rename(columns=final)
    units = file_cfg.get("units") or {}
    for src, dst in final.items():
        factor = units.get(dst, unit_factor(src, dst))
        if factor != 1.0:
            df[dst] = pd.to_numeric(df[dst], errors="coerce") * factor
    # O2 en fracción (0.21) → porcentaje
    if "o2_pct" in df:
        o2 = pd.to_numeric(df["o2_pct"], errors="coerce")
        if o2.dropna().between(0, 1).all() and len(o2.dropna()):
            df["o2_pct"] = o2 * 100

    investigation = file_cfg.get("investigation") or path.stem.split("_")[0].upper()
    return conform(df, investigation=investigation, source=f"PSI:{path.name}",
                   defaults=cfg.get("defaults") or {})


def ingest_all(verbose: bool = False) -> pd.DataFrame:
    cfg = load_config()
    files = sorted(p for p in RAW_PSI_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"})
    if not files:
        print(f"No hay tablas en {RAW_PSI_DIR}. Descárgalas de psi.nasa.gov (ver README).")
        return pd.DataFrame()
    frames = [convert(p, cfg, verbose) for p in files]
    df = pd.concat(frames, ignore_index=True)
    for w in validate(df):
        print("⚠️ ", w)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true", help="sólo mostrar el mapeo de columnas")
    a = ap.parse_args()
    df = ingest_all(verbose=True)
    if a.inspect or df.empty:
        return
    dest = PROCESSED_DIR / "psi_runs.csv"
    df.to_csv(dest, index=False)
    print(f"\n✅ {len(df)} pruebas guardadas en {dest}")


if __name__ == "__main__":
    main()
