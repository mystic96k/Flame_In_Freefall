# Imagen única: backend + dashboard.
# Funciona igual en Hugging Face Spaces (puerto 7860) y en Render (Render define $PORT).
FROM python:3.12-slim

# Hugging Face Spaces corre el contenedor con el usuario 1000
RUN useradd -m -u 1000 app
WORKDIR /home/app/firefall
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app

# Prepara datos y entrena al construir la imagen (tarda segundos).
# Si agregas tablas reales en data/raw/psi/, se usan automáticamente.
RUN python -m pipeline.run_pipeline && python -m ml.train_classifier && python -m ml.train_regressor

ENV PORT=7860
EXPOSE 7860
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
