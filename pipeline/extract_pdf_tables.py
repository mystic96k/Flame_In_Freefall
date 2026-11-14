"""Extrae tablas de pruebas desde reportes PDF de NTRS (plan B si no tienes la Experiment Table).

Muchos artículos publican su matriz de pruebas en un apéndice. Ejemplo real:
el artículo de BASS/BASS-II (NTRS 20150008962) lista en su apéndice las 27
pruebas con tela algodón/fibra de vidrio.

Uso:
    python -m pipeline.fetch_ntrs --pdf 20150008962
    python -m pipeline.extract_pdf_tables data/raw/pdfs/20150008962.pdf --pages 8-12
      → guarda cada tabla como data/raw/psi/<pdf>_p<página>_t<n>.csv
    Revisa los CSV, borra los que no sirvan, renombra el bueno (p. ej. bass2_appendix_table.csv)
    y corre ingest_psi_tables.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pdfplumber

from config.settings import RAW_PSI_DIR


def parse_pages(spec: str | None, n_pages: int) -> list[int]:
    if not spec:
        return list(range(n_pages))
    pages: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a) - 1, int(b)))
        else:
            pages.append(int(part) - 1)
    return [p for p in pages if 0 <= p < n_pages]


def extract(pdf_path: Path, pages: str | None = None, min_rows: int = 4) -> list[Path]:
    saved: list[Path] = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in parse_pages(pages, len(pdf.pages)):
            for i, table in enumerate(pdf.pages[p].extract_tables()):
                rows = [r for r in table if r and any(c not in (None, "") for c in r)]
                if len(rows) < min_rows:
                    continue
                header, *body = rows
                header = [str(h or f"col{j}").replace("\n", " ").strip() for j, h in enumerate(header)]
                df = pd.DataFrame(body, columns=header)
                dest = RAW_PSI_DIR / f"{pdf_path.stem}_p{p + 1}_t{i + 1}.csv"
                df.to_csv(dest, index=False)
                saved.append(dest)
                print(f"✓ página {p + 1}, tabla {i + 1}: {len(df)} filas × {len(header)} columnas → {dest.name}")
    if not saved:
        print("No encontré tablas. Prueba otras páginas o copia la tabla a mano en un CSV.")
    return saved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", help="ej. 8-12 o 3,5,9")
    a = ap.parse_args()
    extract(a.pdf, a.pages)


if __name__ == "__main__":
    main()
