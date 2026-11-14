"""Base de conocimiento para la IA (RAG ligero con TF-IDF, sin base de datos vectorial).

Fuentes:
  - data/knowledge/faq.json           preguntas frecuentes curadas, con fuentes
  - data/knowledge/experiments.json   catálogo curado de experimentos reales
  - data/raw/ntrs/publications.json   resúmenes descargados con pipeline.fetch_ntrs (opcional)

Para cada pregunta se recuperan los fragmentos más parecidos y se pasan al
modelo de lenguaje con su fuente. Así la IA cita y no inventa.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import CATALOG_JSON, FAQ_JSON, RAW_NTRS_DIR


@dataclass
class Chunk:
    id: str
    title: str
    text: str
    source: str
    kind: str  # "faq" | "catalog" | "dataset" | "publication"


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_JSON.read_text(encoding="utf-8")) if CATALOG_JSON.exists() else []


def load_faq() -> list[dict]:
    return json.loads(FAQ_JSON.read_text(encoding="utf-8")) if FAQ_JSON.exists() else []


def _chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for f in load_faq():
        text = f"{f['question']} {' '.join(f.get('keywords', []))}. {f['answer']}"
        chunks.append(Chunk(f["id"], f["question"], text, (f.get("sources") or [""])[0], "faq"))
    for e in load_catalog():
        text = (f"{e['name']} ({e['id']}), {e['platform']}. {e['summary']} "
                f"Hallazgo: {e['finding']} Lección de seguridad: {e['safety']}")
        chunks.append(Chunk(e["id"], e["name"], text, (e.get("sources") or [""])[0], "catalog"))
    try:  # datos reales extra de PSI (gases BASS-II, FLEX, BASS-I, SAFFIRE-I)
        from pipeline.nasa_extra import knowledge_chunks
        for c in knowledge_chunks():
            chunks.append(Chunk(c["id"], c["title"], c["text"], c["source"], "dataset"))
    except Exception:  # noqa: BLE001 - la base de conocimiento no debe romperse por esto
        pass
    pubs = RAW_NTRS_DIR / "publications.json"
    if pubs.exists():
        for p in json.loads(pubs.read_text(encoding="utf-8")):
            if p.get("abstract"):
                chunks.append(Chunk(p["id"], p["title"] or "", f"{p['title']}. {p['abstract']}",
                                    p["url"], "publication"))
    return chunks


class KnowledgeBase:
    def __init__(self) -> None:
        self.chunks = _chunks()
        # Sin stopwords fijas: los textos mezclan español e inglés.
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks]) if self.chunks else None

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        if self.matrix is None:
            return []
        sims = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        order = sims.argsort()[::-1][:k]
        return [(self.chunks[i], float(sims[i])) for i in order if sims[i] > 0.02]


@lru_cache(maxsize=1)
def get_kb() -> KnowledgeBase:
    return KnowledgeBase()
