# 🚀 Publicar FIREFALL en internet (gratis)

Necesitas: cuenta de GitHub y Hugging Face (versión estática) y/o Render + llave gratis de Groq (versión completa).

**Recomendación:** usa las dos. Hugging Face Static como link principal (no se duerme) y Render para mostrar el chat con IA.
Tiempo: ~20 minutos la primera vez.

## Paso 0 — Probar en tu compu
```bash
pip install -r requirements.txt
cp .env.example .env            # pega tu llave de Groq en OPENAI_API_KEY
python -m pipeline.run_pipeline && python -m ml.train_classifier && python -m ml.train_regressor
uvicorn api.main:app --reload   # http://localhost:8000
```
En la sección "Analista IA" debe decir **"IA conectada"**. Si dice "Modo sin LLM", revisa la llave.

## Paso 1 — Llave de Groq
1. Entra a https://console.groq.com/keys → *Create API Key*.
2. Cópiala (empieza con `gsk_`). **No la subas a GitHub.**
3. Verifica el nombre del modelo en https://console.groq.com/docs/models; si `llama-3.3-70b-versatile` ya no aparece, cambia `OPENAI_MODEL`.

## Paso 2 — Subir el código a GitHub
```bash
git init
git add .
git commit -m "FIREFALL: primera versión"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/firefall.git
git push -u origin main
```
El `.gitignore` ya excluye `.env`. Space Apps pide que el código esté en un repositorio público.

## Opción A0 — GitHub Pages (la más fácil, ya está preparada)
La carpeta `docs/` del repo es la versión sin servidor. Sólo la dueña del repo tiene que activarla una vez:
1. En GitHub, abre el repo → **Settings** → **Pages** (menú izquierdo).
2. En **Source** elige **Deploy from a branch**.
3. En **Branch** elige **main** y la carpeta **/docs** → **Save**.
4. En 1–2 minutos aparece arriba el link: `https://mystic96k.github.io/Flame_In_Freefall/`
Cada vez que se haga push a `main`, la página se actualiza sola.

## Opción A — Hugging Face **Static** (gratis, siempre encendido)
Desde julio de 2026 las cuentas gratis de Hugging Face sólo pueden crear Spaces **Static**
(Docker y Gradio piden plan de pago). Por eso existe la carpeta **`docs/`**: una versión
del dashboard que no necesita servidor. Python ya hizo todo el cálculo y el navegador evalúa el modelo.

Qué funciona: simulador, gráfica con frontera del modelo, hallazgos, catálogo y reporte de seguridad.
Qué no: el chat con modelo de lenguaje (Groq). Una llave en una página pública quedaría expuesta,
así que el analista responde con el modelo de ML + las fuentes NASA.

1. https://huggingface.co/new-space → nombre `firefall`, **SDK: Static**, *Blank*, **Public** → *Create Space*.
2. Pestaña **Files → + Add file → Upload files**.
3. Abre la carpeta **`docs`** del repo, selecciona **todo lo de adentro**
   (`index.html`, `README.md`, `css`, `js`, `data`) y arrástralo.
4. *Commit changes to main*. Si pregunta por reemplazar `README.md`, di que sí.
5. En segundos queda en: `https://TU_USUARIO-firefall.static.hf.space` (el botón ⋮ → *Embed this Space* te muestra el link directo).

¿Cambiaste datos o el modelo? Regenera la carpeta antes de subirla:
```bash
python -m pipeline.run_pipeline && python -m ml.train_classifier && python -m ml.export_static
```
La misma carpeta `docs/` sirve para **GitHub Pages** (Settings → Pages).

## Opción B — Render (versión completa con IA de Groq)
1. https://dashboard.render.com → *New → Blueprint* → conecta tu repo. Render lee `render.yaml`.
2. Cuando lo pida, pega tu llave de Groq en `OPENAI_API_KEY`.
3. Link: `https://firefall.onrender.com` (o el nombre que te asigne).
4. ⚠️ El plan gratis se duerme tras 15 minutos sin visitas y tarda en despertar.
   **Abre el link 2 minutos antes de presentar**, o programa un "ping" a `/api/health` cada 10 minutos (p. ej. cron-job.org).

## Paso 3 — Revisión antes de entregar
- [ ] (Render) `https://TU-LINK/api/health` responde `"llm": true`
- [ ] El simulador cambia al mover los sliders (ISS → Tierra)
- [ ] La gráfica muestra puntos y la línea de frontera
- [ ] El analista responde con fuentes `[BASS]`, `[SAFFIRE]`…
- [ ] (Static) Abre el Space en una ventana de incógnito para confirmar que es público
- [ ] (Render) `https://TU-LINK/docs` abre la documentación de la API (impresiona a jueces técnicos)
- [ ] El link del repo y del demo están en la página del proyecto de Space Apps

## Si algo falla
| Síntoma | Causa probable | Solución |
|---|---|---|
| "No pude conectar con el backend" | El servicio se está despertando | Espera ~1 min y recarga |
| "Modo sin LLM" | Falta la llave o el nombre del modelo cambió | Revisa secrets y `OPENAI_MODEL` |
| `429` en el chat | Límite gratis de Groq | Espera un minuto; el demo sigue funcionando sin LLM |
| Build falla en `pip install` | Versión de Python | La imagen usa 3.12; no cambies el `FROM` |
