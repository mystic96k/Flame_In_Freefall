# 🚀 Publicar FIREFALL en internet (gratis)

Necesitas: cuenta de GitHub, una llave gratis de Groq, y Hugging Face **o** Render.
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

## Opción A (recomendada) — Hugging Face Spaces
Ventaja: más memoria que el plan gratis de Render y no se duerme cada 15 minutos.
1. https://huggingface.co/new-space → nombre `firefall`, **SDK: Docker**, plantilla *Blank*, hardware *CPU basic (free)*.
2. En el Space: *Settings → Variables and secrets*:
   - Secret `OPENAI_API_KEY` = tu llave de Groq
   - Variables `LLM_PROVIDER=openai_compatible`, `OPENAI_BASE_URL=https://api.groq.com/openai/v1`, `OPENAI_MODEL=llama-3.3-70b-versatile`
3. Sube el código (el Space es un repo git):
   ```bash
   git remote add space https://huggingface.co/spaces/TU_USUARIO/firefall
   git push space main
   ```
   El `README.md` ya trae el encabezado que Hugging Face necesita (`sdk: docker`, `app_port: 7860`).
4. Espera a que el estado diga *Running*. Tu link: `https://TU_USUARIO-firefall.hf.space`

## Opción B — Render
1. https://dashboard.render.com → *New → Blueprint* → conecta tu repo. Render lee `render.yaml`.
2. Cuando lo pida, pega tu llave de Groq en `OPENAI_API_KEY`.
3. Link: `https://firefall.onrender.com` (o el nombre que te asigne).
4. ⚠️ El plan gratis se duerme tras 15 minutos sin visitas y tarda en despertar.
   **Abre el link 2 minutos antes de presentar**, o programa un "ping" a `/api/health` cada 10 minutos (p. ej. cron-job.org).

## Paso 3 — Revisión antes de entregar
- [ ] `https://TU-LINK/api/health` responde `"llm": true`
- [ ] El simulador cambia al mover los sliders (ISS → Tierra)
- [ ] La gráfica muestra puntos y la línea de frontera
- [ ] El analista responde con fuentes `[BASS]`, `[SAFFIRE]`…
- [ ] `https://TU-LINK/docs` abre la documentación de la API (impresiona a jueces técnicos)
- [ ] El link del repo y del demo están en la página del proyecto de Space Apps

## Si algo falla
| Síntoma | Causa probable | Solución |
|---|---|---|
| "No pude conectar con el backend" | El servicio se está despertando | Espera ~1 min y recarga |
| "Modo sin LLM" | Falta la llave o el nombre del modelo cambió | Revisa secrets y `OPENAI_MODEL` |
| `429` en el chat | Límite gratis de Groq | Espera un minuto; el demo sigue funcionando sin LLM |
| Build falla en `pip install` | Versión de Python | La imagen usa 3.12; no cambies el `FROM` |
