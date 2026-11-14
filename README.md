---
title: FIREFALL
emoji: 🔥
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🔥 FIREFALL — Seguridad contra incendios en microgravedad con IA

Proyecto para el reto **"Flame in Freefall"** de NASA Space Apps 2026.
Resume, clasifica e interpreta datos de combustión en microgravedad de la NASA para ayudar a diseñar
naves y hábitats más seguros.

---

## 1. Arquitectura

```
 FUENTES NASA                     PIPELINE (Python)                ML (scikit-learn)            BACKEND (FastAPI)          FRONTEND
 ───────────                      ────────────────                 ─────────────────            ─────────────────          ────────
 PSI (Experiment Tables) ──► ingest_psi_tables ─┐
 NTRS (PDF con tablas)   ──► extract_pdf_tables ┤                   train_classifier ──┐
                                                ├─► schema.conform ─► runs.csv ──────► train_regressor ──┼─► predict.py ─┐
 Datos de demostración   ──► make_demo_data ────┘   (validación)    features.py        insights.py ─────┘               ├─► /api/* ──► Dashboard
                                                                                                                         │              (simulador, gráficas,
 NTRS (resúmenes)        ──► fetch_ntrs ──────────► knowledge_base (TF-IDF / RAG) ──► analyst.py ──► llm_client ────────┘               catálogo, chat IA)
 Catálogo curado         ──► experiments.json ────┘
 NASA Image Library      ──► fetch_images ──► galería (opcional)
```

| Capa | Carpeta | Qué hace |
|---|---|---|
| Configuración | `config/` | rutas, variables de entorno, mapeo de columnas |
| Datos | `data/` | `raw/` (tal cual de la NASA) → `processed/runs.csv` (limpio) |
| Pipeline | `pipeline/` | descarga, extracción, normalización, validación, variables físicas |
| Machine Learning | `ml/` | clasificador (¿arde o se apaga?), regresor (velocidad de propagación), hallazgos |
| IA | `ai/` | búsqueda en fuentes (RAG con TF-IDF) + modelo de lenguaje con cualquier proveedor |
| API | `api/` | FastAPI: `/api/predict`, `/api/runs`, `/api/boundary`, `/api/insights`, `/api/ask`, `/api/report` |
| Frontend | `frontend/` | HTML + CSS + JS en módulos, Chart.js, animación en canvas |
| Pruebas | `tests/` | pytest de pipeline y API |

```
firefall-app/
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── Makefile
├── render.yaml               despliegue en Render
├── DEPLOY.md                 guía para publicar online
├── config/
│   ├── settings.py
│   └── column_maps.yaml
├── data/
│   ├── raw/psi/              ← aquí van las Experiment Tables que descargues
│   ├── raw/pdfs/  raw/ntrs/  raw/images/
│   ├── processed/runs.csv
│   ├── sample/demo_runs.csv
│   └── knowledge/experiments.json
├── pipeline/
│   ├── schema.py             esquema estándar + normalización + validación
│   ├── features.py           flujo efectivo (ventilación + flotación)
│   ├── fetch_ntrs.py         publicaciones NTRS (API pública)
│   ├── fetch_images.py       fotos NASA (API pública)
│   ├── fetch_psi_s3.py       bucket público s3://nasa-psi
│   ├── ingest_psi_tables.py  Experiment Tables → esquema estándar
│   ├── extract_pdf_tables.py tablas de pruebas desde PDFs
│   ├── make_demo_data.py     datos sintéticos (marcados is_demo)
│   └── run_pipeline.py       orquestador
├── ml/
│   ├── train_classifier.py   compara 3 modelos con validación cruzada
│   ├── train_regressor.py    velocidad de propagación
│   ├── predict.py            probabilidad, O₂ límite, fronteras
│   ├── insights.py           hallazgos en lenguaje natural
│   └── artifacts/            modelos .joblib + métricas .json
├── ai/
│   ├── knowledge_base.py     RAG con TF-IDF
│   ├── prompts.py
│   ├── llm_client.py         Anthropic / compatible con OpenAI / sin IA
│   └── analyst.py
├── api/
│   ├── main.py
│   └── schemas.py
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/ api.js state.js flame.js simulator.js charts.js catalog.js chat.js main.js
└── tests/
```

## 2. Arranque rápido (5 minutos)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # opcional: pon tu llave de IA

python -m pipeline.run_pipeline     # sin datos reales usa el dataset de demostración
python -m ml.train_classifier
python -m ml.train_regressor
uvicorn api.main:app --reload       # abre http://localhost:8000  y  /docs
pytest -q                           # 9 pruebas
```

## 3. Cómo conseguir datos REALES de la NASA

### A. NASA PSI — la fuente principal (datos de pruebas)
Physical Sciences Informatics es el repositorio abierto de experimentos de ciencias físicas en microgravedad.
Investigaciones de **combustión** listadas en PSI: **BASS, FLEX, FLEX-2, ACME S-Flames, SLICE, SPICE, DAFT, DAFT-2**.

1. Entra a **https://psi.nasa.gov** (si te pide registro, es gratis).
2. Filtra *Research Area → Combustion Science* y abre una investigación (empieza por **BASS**: sólidos + flujo + oxígeno, ideal para el clasificador).
3. En la página de la investigación busca **Experiment Table** (la matriz de pruebas). Se descarga desde *Data Files and Documents*.
4. Guárdala en `data/raw/psi/` con un nombre descriptivo (ej. `bass_experiment_table.xlsx`).
5. Revisa el mapeo de columnas:
   ```bash
   python -m pipeline.ingest_psi_tables --inspect
   ```
   Si alguna columna quedó mal, corrígela en `config/column_maps.yaml`.
6. Regenera y reentrena:
   ```bash
   python -m pipeline.run_pipeline && python -m ml.train_classifier && python -m ml.train_regressor
   ```
   El aviso de "datos de demostración" desaparece solo.

> PSI también está en AWS: `aws s3 ls --no-sign-request s3://nasa-psi/` (o `python -m pipeline.fetch_psi_s3 --list`).
> El registro de AWS lo describe como datos de DSI y OASIS, así que es probable que la combustión esté sólo en el portal.

### B. Plan B: tablas dentro de reportes técnicos (NTRS)
Muchos artículos publican su matriz de pruebas. Ejemplo: el artículo de BASS/BASS-II (NTRS **20150008962**)
tiene en su apéndice la lista de las 27 pruebas con tela algodón/fibra de vidrio.
```bash
python -m pipeline.fetch_ntrs --pdf 20150008962
python -m pipeline.extract_pdf_tables data/raw/pdfs/20150008962.pdf
# revisa los CSV generados en data/raw/psi/, quédate con el bueno y renómbralo
```
Otros reportes con datos: FLEX (NASA/TP-2015-216046, 284 pruebas), Saffire (ICES 2017 y 2021).

### C. Publicaciones para la IA (RAG)
```bash
python -m pipeline.fetch_ntrs              # guarda resúmenes en data/raw/ntrs/publications.json
```
El analista IA los indexa automáticamente y cita el ID de NTRS en sus respuestas. API pública, sin llave.

### D. Imágenes reales
```bash
python -m pipeline.fetch_images            # metadatos + miniaturas de images-api.nasa.gov
```
Crédito: NASA. Útiles para slides y para una galería "imagen real vs. simulación".

## 4. Machine Learning (qué decir a los jueces)

- **Problema:** clasificación binaria — ¿la llama se sostiene (1) o se apaga (0)?
- **Variables con sentido físico:** oxígeno, presión, material y **flujo efectivo** = √(ventilación² + (40·g)²).
  El término (log flujo)² deja que el modelo aprenda la curva en "U": con poco flujo la llama se ahoga, con mucho se sopla.
- **Modelos comparados:** regresión logística, random forest, gradient boosting, con validación cruzada estratificada.
  Se elige la logística si está empatada: es interpretable y extrapola mejor con pocos datos.
- **Explicabilidad:** importancia por permutación (gráfica "¿qué pesa más?").
- **Salida útil:** O₂ límite para cualquier escenario (búsqueda binaria sobre el modelo) y fronteras por material.
- **Honestidad:** la API marca `extrapolating=true` cuando se sale del rango de los datos (p. ej. gravedad lunar).

## 5. IA

`LLM_PROVIDER` en `.env`: `openai_compatible` (por defecto Groq gratis; también Ollama local u OpenAI), `anthropic` o `none`.
Con `none` el demo sigue funcionando con respuestas automáticas del modelo + fuentes, así que nunca se queda en blanco.
La llave vive sólo en el backend.

## 6. Despliegue

Guía paso a paso en **[DEPLOY.md](DEPLOY.md)**: Hugging Face Spaces (recomendado) o Render, con IA gratis de Groq.

- **Docker local:** `docker build -t firefall . && docker run -p 7860:7860 --env-file .env firefall`
- **Frontend separado (GitHub Pages):** sube `frontend/` y define `window.FIREFALL_API = "https://tu-backend"` antes de `main.js`.

## 7. Fuentes
- NASA PSI: https://psi.nasa.gov · https://registry.opendata.aws/nasa-psi
- NTRS API: https://ntrs.nasa.gov/api/openapi/
- NASA Image and Video Library API: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
- Investigaciones de PSI por área: https://www.nasa.gov/physical-sciences-informatics-psi/psi-investigations-by-research-area/
