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
├── docs/              versión sin servidor lista para Hugging Face Static
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
│   ├── export_static.py      exporta la versión sin servidor
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

## 3. Datos REALES que ya usa el proyecto

El modelo está entrenado con la **tabla de pruebas real de BASS / BASS-II** (tela algodón/fibra de vidrio SIBAL, ISS, 1 atm):
apéndice de Zhao, T'ien, Ferkul y Olson (2015), [NTRS 20150008962](https://ntrs.nasa.gov/citations/20150008962).
- Transcripción original: `data/raw/ntrs/bass2_appendix_raw.csv` (31 pruebas)
- Conversión a observaciones: `python -m pipeline.bass2_appendix` → `data/raw/psi/bass2_observations.csv` (48 observaciones;
  una prueba con flujo cambiado "10→2.2 cm/s" aporta dos: antes y después del cambio)
- Las pruebas "sin ignición" se muestran pero el modelo no las usa (no encender ≠ apagarse); las de muestras reutilizadas que no encendieron se excluyen.

**Más datos reales (sección 04 del panel)** — `python -m pipeline.nasa_extra` (también lo corre `run_pipeline`) → `data/processed/extra.json`:

| Fuente (NASA PSI, CC0) | Archivo | Qué se hace |
| --- | --- | --- |
| [PSI-25 BASS-II](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) · DOI 10.60555/4qc4-de67 | `data/raw/nasa/psi25_bass2_gases_raw.csv` (129 pruebas) | O₂ consumido, CO₂ y CO generados por material; CO/CO₂ como indicador de combustión incompleta |
| [PSI-69 FLEX](https://psi.nasa.gov/physci/repo/data/investigations/PSI-69) · DOI 10.60555/mbq8-0451 | `data/raw/nasa/psi69_flex_rows_p*.txt` (274 gotas) | 2.º modelo ML: ¿se apaga la llama antes de terminar la gota? (AUC 0.83) + D_ext/D₀ con bosque aleatorio (R² 0.63) |
| [PSI-26 BASS-I](https://psi.nasa.gov/physci/repo/data/investigations/PSI-26) · DOI 10.60555/58h4-dy80 | en `pipeline/nasa_extra.py` | Inventario de 122 pruebas por material |
| [PSI-98 SAFFIRE-I](https://psi.nasa.gov/physci/repo/data/investigations/PSI-98) · DOI 10.60555/0t15-1z43 | en `pipeline/nasa_extra.py` | 420 s (a favor del flujo) vs 70 s (en contra) |

Nota: la tabla web de FLEX omite celdas vacías; los valores faltantes se asignan por posición. Para análisis finos, descarga
`PSI-69_Experimental table_FLEX.csv` desde la página de PSI.

La IA usa además `data/knowledge/faq.json` (23 preguntas frecuentes curadas con fuentes), `experiments.json` (11 experimentos,
incluidos E-FIELD, BRE y Candle Flames en la Mir) y los resúmenes de los datasets anteriores.

## 3b. Cómo conseguir MÁS datos reales de la NASA

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

**Bilingüe (ES / EN):** botón ES · EN en la barra superior, o `?lang=en` en la URL. Los textos de la interfaz están en `frontend/js/i18n.js`; los datos traen campos `*_en` (catálogo, FAQ, hallazgos) y la IA responde en el idioma elegido (`lang` en `/api/ask` y `/api/report`).

`LLM_PROVIDER` en `.env`: `openai_compatible` (por defecto Groq gratis; también Ollama local u OpenAI), `anthropic` o `none`.
Con `none` el demo sigue funcionando con respuestas automáticas del modelo + fuentes, así que nunca se queda en blanco.
La llave vive sólo en el backend.

## 6. Despliegue

Guía paso a paso en **[DEPLOY.md](DEPLOY.md)**:
- **Hugging Face Static / GitHub Pages:** sube la carpeta `docs/` (generada con `python -m ml.export_static`). Sin servidor; el modelo corre en el navegador.
- **Render:** versión completa con backend e IA gratis de Groq (`render.yaml`).

- **Docker local:** `docker build -t firefall . && docker run -p 7860:7860 --env-file .env firefall`
- **Frontend separado (GitHub Pages):** sube `frontend/` y define `window.FIREFALL_API = "https://tu-backend"` antes de `main.js`.

## 7. Fuentes
- NASA PSI: https://psi.nasa.gov · https://registry.opendata.aws/nasa-psi
- NTRS API: https://ntrs.nasa.gov/api/openapi/
- NASA Image and Video Library API: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
- Investigaciones de PSI por área: https://www.nasa.gov/physical-sciences-informatics-psi/psi-investigations-by-research-area/
