# Atajos (en Windows usa los comandos de la derecha directamente)
.PHONY: install data real train serve test all

install:
	pip install -r requirements.txt

data:            ## datos (reales si hay en data/raw/psi, si no demo)
	python -m pipeline.run_pipeline

real:            ## descarga publicaciones e imágenes de la NASA
	python -m pipeline.fetch_ntrs
	python -m pipeline.fetch_images

train:
	python -m ml.train_classifier
	python -m ml.train_regressor

serve:
	uvicorn api.main:app --reload

test:
	pytest -q

all: data train serve
