"""Descarga metadatos y resúmenes de publicaciones del NASA Technical Reports Server (NTRS).

La API pública no requiere llave: https://ntrs.nasa.gov/api/openapi/
Los resúmenes alimentan la base de conocimiento de la IA (RAG) y el catálogo.

Uso:
    python -m pipeline.fetch_ntrs                      # consultas por defecto
    python -m pipeline.fetch_ntrs --q "BASS flame spread" --max 40
    python -m pipeline.fetch_ntrs --pdf 20150008962    # descarga el PDF de una cita
"""
from __future__ import annotations

import argparse
import json
import time

import httpx

from config.settings import RAW_NTRS_DIR, RAW_PDF_DIR

API = "https://ntrs.nasa.gov/api"
DEFAULT_QUERIES = [
    "microgravity flame spread solid fuel",
    "Burning and Suppression of Solids BASS",
    "Flame Extinguishment Experiment FLEX droplet",
    "Saffire spacecraft fire safety",
    "SoFIE solid fuel ignition extinction",
    "ACME microgravity flames",
    "spacecraft material flammability oxygen concentration",
    "cool flame microgravity",
]


def search(query: str, max_results: int = 25) -> list[dict]:
    """Busca en NTRS y regresa registros simplificados."""
    size = min(max_results, 100)
    # La API acepta POST con JSON (recomendado); el GET con parámetros quedó como "deprecated".
    r = httpx.post(f"{API}/citations/search", json={"q": query, "page": {"size": size, "from": 0}}, timeout=30)
    if r.status_code >= 400:
        r = httpx.get(f"{API}/citations/search", params={"q": query, "page.size": size}, timeout=30)
    r.raise_for_status()
    out = []
    for item in r.json().get("results", []):
        out.append({
            "id": str(item.get("id")),
            "title": item.get("title"),
            "abstract": item.get("abstract"),
            "year": (item.get("publications") or [{}])[0].get("publicationDate", "")[:4]
                    if item.get("publications") else str(item.get("created", ""))[:4],
            "authors": [a.get("meta", {}).get("author", {}).get("name")
                        for a in item.get("authorAffiliations", [])][:6],
            "keywords": item.get("keywords", []),
            "url": f"https://ntrs.nasa.gov/citations/{item.get('id')}",
            "pdf": next((f"https://ntrs.nasa.gov{d['links']['pdf']}"
                         for d in item.get("downloads", []) if d.get("links", {}).get("pdf")), None),
            "query": query,
        })
    return out


def download_pdf(citation_id: str) -> str:
    """Descarga el PDF de una cita a data/raw/pdfs/<id>.pdf."""
    meta = httpx.get(f"{API}/citations/{citation_id}", timeout=30).json()
    links = [d["links"]["pdf"] for d in meta.get("downloads", []) if d.get("links", {}).get("pdf")]
    if not links:
        raise SystemExit(f"La cita {citation_id} no tiene PDF público.")
    url = f"https://ntrs.nasa.gov{links[0]}"
    dest = RAW_PDF_DIR / f"{citation_id}.pdf"
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    print(f"PDF guardado en {dest}")
    return str(dest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--q", action="append", help="consulta (puedes repetir)")
    ap.add_argument("--max", type=int, default=25)
    ap.add_argument("--pdf", help="id de cita NTRS para descargar su PDF")
    args = ap.parse_args()

    if args.pdf:
        download_pdf(args.pdf)
        return

    seen: dict[str, dict] = {}
    for q in args.q or DEFAULT_QUERIES:
        try:
            for rec in search(q, args.max):
                seen.setdefault(rec["id"], rec)
            print(f"✓ {q!r}: total acumulado {len(seen)}")
        except httpx.HTTPError as e:
            print(f"✗ {q!r}: {e}")
        time.sleep(0.5)  # sé amable con la API

    dest = RAW_NTRS_DIR / "publications.json"
    dest.write_text(json.dumps(list(seen.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardé {len(seen)} publicaciones en {dest}")


if __name__ == "__main__":
    main()
