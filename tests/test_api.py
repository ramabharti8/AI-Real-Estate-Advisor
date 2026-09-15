import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "area_sqft": 1200,
    "city": "Pune",
    "locality": "Kothrud",
    "bedrooms": 2,
    "bathrooms": 2,
    "age_years": 5,
    "furnishing": "Semi-Furnished",
    "parking": 1,
    "amenities_score": 6.0,
}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_predict_success():
    resp = client.post("/predict", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_price"] > 0
    assert "predicted_price_formatted" in body


def test_predict_validation_error():
    bad_payload = {**VALID_PAYLOAD, "area_sqft": -10}
    resp = client.post("/predict", json=bad_payload)
    assert resp.status_code == 422


def test_predict_invalid_city_rejected():
    bad_payload = {**VALID_PAYLOAD, "city": "Atlantis"}
    resp = client.post("/predict", json=bad_payload)
    assert resp.status_code == 422


def test_insights_template_fallback_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    payload = {**VALID_PAYLOAD, "predicted_price": 8500000}
    resp = client.post("/insights", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "template"
    assert len(body["insight"]) > 0
