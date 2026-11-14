"""Busca fotos y videos reales de llamas en microgravedad en la NASA Image and Video Library.

API pública sin llave: https://images-api.nasa.gov
Guarda sólo metadatos y enlaces (no descarga los archivos), para mostrarlos en
la galería del dashboard con su crédito correspondiente.

Uso:
    python -m pipeline.fetch_images
    python -m pipeline.fetch_images --q "FLEX droplet" --q "Saffire"
"""
from __future__ import annotations

import argparse
import json

import httpx

from config.settings import RAW_IMAGES_DIR

API = "https://images-api.nasa.gov/search"
DEFAULT_QUERIES = ["microgravity flame", "Combustion Integrated Rack", "FLEX flame",
                   "BASS flame", "Saffire fire", "ACME flame", "SoFIE"]


def search(query: str, page_size: int = 30) -> list[dict]:
    r = httpx.get(API, params={"q": query, "media_type": "image", "page_size": page_size}, timeout=30)
    r.raise_for_status()
    out = []
    for item in r.json().get("collection", {}).get("items", []):
        data = (item.get("data") or [{}])[0]
        thumb = next((l["href"] for l in item.get("links", []) if l.get("rel") == "preview"), None)
        out.append({
            "nasa_id": data.get("nasa_id"),
            "title": data.get("title"),
            "description": (data.get("description") or "")[:600],
            "date": (data.get("date_created") or "")[:10],
            "center": data.get("center"),
            "keywords": data.get("keywords", []),
            "thumbnail": thumb,
            "page": f"https://images.nasa.gov/details/{data.get('nasa_id')}",
            "credit": "NASA",
            "query": query,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", action="append")
    args = ap.parse_args()
    seen: dict[str, dict] = {}
    for q in args.q or DEFAULT_QUERIES:
        try:
            for rec in search(q):
                if rec["nasa_id"]:
                    seen.setdefault(rec["nasa_id"], rec)
            print(f"✓ {q!r}: {len(seen)} imágenes acumuladas")
        except httpx.HTTPError as e:
            print(f"✗ {q!r}: {e}")
    dest = RAW_IMAGES_DIR / "images.json"
    dest.write_text(json.dumps(list(seen.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardé {len(seen)} registros en {dest}")


if __name__ == "__main__":
    main()
