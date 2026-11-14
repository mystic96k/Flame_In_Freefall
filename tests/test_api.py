"""Pruebas de punta a punta: datos de demo → entrenamiento → API."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from ml import train_classifier, train_regressor
    from ml.predict import reload_models
    from pipeline import run_pipeline

    run_pipeline.build(force_demo=True)
    train_classifier.train()
    train_regressor.train()
    reload_models()
    from api.main import app
    yield TestClient(app)
    # Restaurar los datos reales para no dejar el proyecto con datos de demostración
    run_pipeline.build()
    train_classifier.train()
    train_regressor.train()
    reload_models()


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_predict_monotonic_in_oxygen(client):
    low = client.post("/api/predict", json={"material": "PMMA", "o2_pct": 14, "flow_cm_s": 10}).json()
    high = client.post("/api/predict", json={"material": "PMMA", "o2_pct": 30, "flow_cm_s": 10}).json()
    assert high["burn_probability"] > low["burn_probability"]
    assert high["state"] == "burning"


def test_quiescent_is_safer_than_ventilated(client):
    still = client.post("/api/predict", json={"material": "PMMA", "o2_pct": 21, "flow_cm_s": 0.5}).json()
    vent = client.post("/api/predict", json={"material": "PMMA", "o2_pct": 21, "flow_cm_s": 10}).json()
    assert vent["burn_probability"] > still["burn_probability"]


def test_catalog_and_insights(client):
    assert len(client.get("/api/catalog").json()) >= 5
    assert len(client.get("/api/insights").json()) >= 3


def test_ask_offline(client):
    r = client.post("/api/ask", json={"question": "¿Qué aprendimos de Saffire?"}).json()
    assert r["mode"] in {"offline", "llm"}
    assert any(s["id"] in {"SAFFIRE", "FAQ-SAFFIRE"} for s in r["sources"])


def test_faq_answers_spherical_flame(client):
    r = client.post("/api/ask", json={"question": "¿Por qué la llama es esférica en el espacio?"}).json()
    assert r["sources"][0]["id"] == "FAQ-ESFERA"


def test_extra(client):
    r = client.get("/api/extra")
    assert r.status_code == 200
    assert r.json()["flex"]["n_tests"] == 274


def test_ask_in_english(client):
    r = client.post("/api/ask", json={"question": "What toxic gases does a spacecraft fire leave behind?", "lang": "en"})
    assert r.status_code == 200
    if r.json()["mode"] == "offline":
        assert "knowledge base" in r.json()["answer"] or "Scenario" in r.json()["answer"]
    assert client.post("/api/report?lang=en", json={}).status_code == 200
