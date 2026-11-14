"""Configuración central: rutas del proyecto y variables de entorno."""
from __future__ import annotations

import os
from pathlib import Path

try:  # python-dotenv es opcional
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"                 # lo que descargas tal cual de la NASA
RAW_PSI_DIR = RAW_DIR / "psi"              # Experiment Tables (.csv / .xlsx)
RAW_PDF_DIR = RAW_DIR / "pdfs"             # reportes técnicos de NTRS
RAW_NTRS_DIR = RAW_DIR / "ntrs"            # metadatos de publicaciones (JSON)
RAW_IMAGES_DIR = RAW_DIR / "images"        # metadatos de imágenes (JSON)
PROCESSED_DIR = DATA_DIR / "processed"     # datos limpios listos para ML
SAMPLE_DIR = DATA_DIR / "sample"           # dataset de demostración
KNOWLEDGE_DIR = DATA_DIR / "knowledge"     # catálogo curado + base de conocimiento de la IA
MODELS_DIR = ROOT / "ml" / "artifacts"     # modelos entrenados y métricas

RUNS_CSV = PROCESSED_DIR / "runs.csv"
DEMO_CSV = SAMPLE_DIR / "demo_runs.csv"
CATALOG_JSON = KNOWLEDGE_DIR / "experiments.json"
COLUMN_MAP_YAML = ROOT / "config" / "column_maps.yaml"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ALLOW_DEMO_DATA = os.getenv("ALLOW_DEMO_DATA", "true").lower() == "true"

# Velocidad equivalente de flotación a 1 g (cm/s). Sirve para comparar
# microgravedad, Luna, Marte y Tierra con una sola variable de "flujo efectivo".
BUOYANT_FLOW_1G = 40.0

for d in (RAW_PSI_DIR, RAW_PDF_DIR, RAW_NTRS_DIR, RAW_IMAGES_DIR, PROCESSED_DIR,
          SAMPLE_DIR, KNOWLEDGE_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)
