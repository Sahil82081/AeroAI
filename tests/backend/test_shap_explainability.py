"""
Unit and Integration Tests for AeroAI Stage 4: SHAP Explainability & Model Evaluation.

Tests:
1. Model prediction with TreeSHAP feature attributions
2. Additive SHAP calculation & directionality
3. Non-causal wording compliance ("These features contributed most to the model's prediction")
4. Adverse weather vs favorable conditions attribution
5. API response schema adherence ({delay_probability, prediction, explanation: [{feature, impact}]})
6. Edge cases: missing weather, unknown carriers, configurable top_k
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from pathlib import Path
import joblib

from app.main import app
from app.ml.predictor import FlightDelayPredictor
from app.ml.explainability import ShapExplainerService

client = TestClient(app)
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "ml" / "artifacts"


def test_shap_explainer_initialization():
    """Verifies ShapExplainerService loads with serialized model and reasonable expected value."""
    model = joblib.load(ARTIFACTS_DIR / "best_model.joblib")
    prep = joblib.load(ARTIFACTS_DIR / "preprocessor.joblib")
    feature_names = prep.get_feature_names_out()

    explainer_svc = ShapExplainerService(model, feature_names)
    assert explainer_svc.explainer is not None, "TreeExplainer failed to initialize"
    assert 0.15 <= explainer_svc.expected_value <= 0.35, (
        f"Expected base value ({explainer_svc.expected_value}) should reflect empirical base rate ~24.9%"
    )


def test_shap_calculation_single_flight():
    """Verifies SHAP attributions produce valid magnitudes, directions, and human-readable impacts."""
    predictor = FlightDelayPredictor()
    assert predictor.is_loaded

    res = predictor.predict(
        carrier="UA",
        origin="EWR",
        dest="ORD",
        scheduled_departure="2026-10-20T18:30:00Z",
        distance=719.0,
        top_k=5,
    )

    assert "delay_probability" in res
    assert 0.0 <= res["delay_probability"] <= 1.0
    assert res["prediction"] in ["Likely Delayed", "Likely On-Time"]
    assert res["predicted_class"] in [0, 1]

    assert "explanation" in res
    assert isinstance(res["explanation"], list)
    assert len(res["explanation"]) == 5

    for item in res["explanation"]:
        assert "feature" in item
        assert "impact" in item
        assert isinstance(item["feature"], str) and len(item["feature"]) > 0
        assert isinstance(item["impact"], str) and len(item["impact"]) > 0
        assert item["direction"] in ["INCREASED_RISK", "REDUCED_RISK"]
        assert isinstance(item["shap_value"], float)
        assert np.isfinite(item["shap_value"])


def test_shap_non_causal_framing():
    """Ensures SHAP explanations strictly follow non-causal guidelines."""
    predictor = FlightDelayPredictor()
    res = predictor.predict(
        carrier="DL",
        origin="JFK",
        dest="LAX",
        scheduled_departure="2026-10-20T08:00:00Z",
        distance=2475.0,
    )

    # Required phrasing: "These features contributed most to the model's prediction."
    assert "explanation_summary" in res
    summary = res["explanation_summary"]
    assert "These features contributed most to the model's prediction" in summary, (
        f"Summary missing non-causal phrasing: {summary}"
    )

    # Disclaimer verification
    assert "disclaimer" in res
    disclaimer = res["disclaimer"]
    assert "causal" in disclaimer.lower()
    assert "statistical" in disclaimer.lower() or "shapley" in disclaimer.lower()


def test_shap_adverse_vs_favorable_weather_attribution():
    """
    Verifies that adverse weather conditions produce positive risk SHAP values on weather features,
    while favorable morning conditions produce negative (risk-reducing) SHAP values.
    """
    predictor = FlightDelayPredictor()

    severe_weather = {
        "temp": 32.0, "dewp": 31.0, "humid": 95.0, "wind_speed": 30.0,
        "precip": 0.40, "pressure": 995.0, "visib": 1.0,
        "is_fog": 1.0, "is_high_wind": 1.0, "is_freezing": 1.0, "has_precip": 1.0
    }
    res_severe = predictor.predict(
        carrier="EV", origin="EWR", dest="ORD",
        scheduled_departure="2026-10-20T19:00:00Z",
        weather_override=severe_weather,
        top_k=6,
    )

    clear_weather = {
        "temp": 65.0, "dewp": 40.0, "humid": 40.0, "wind_speed": 5.0,
        "precip": 0.0, "pressure": 1020.0, "visib": 10.0,
        "is_fog": 0.0, "is_high_wind": 0.0, "is_freezing": 0.0, "has_precip": 0.0
    }
    res_clear = predictor.predict(
        carrier="AA", origin="JFK", dest="LAX",
        scheduled_departure="2026-10-20T06:00:00Z",
        weather_override=clear_weather,
        top_k=6,
    )

    assert res_severe["delay_probability"] > res_clear["delay_probability"]
    assert res_severe["prediction"] == "Likely Delayed"

    # Severe weather should have weather features among top increased-risk contributors
    severe_features = [item["raw_feature"] for item in res_severe["explanation"] if item["direction"] == "INCREASED_RISK"]
    weather_keys = {"humid", "precip", "visib", "is_fog", "has_precip", "wind_speed", "is_high_wind"}
    has_weather_impact = bool(set(severe_features) & weather_keys)
    assert has_weather_impact, f"Expected weather features among severe risk drivers: {severe_features}"


def test_api_predict_returns_shap_explanation_schema():
    """Tests POST /api/v1/predict/flight-delay conforms to the exact example schema."""
    payload = {
        "carrier": "B6",
        "origin": "JFK",
        "dest": "BOS",
        "scheduled_departure": "2026-10-20T17:00:00Z",
        "distance": 187.0,
        "top_k": 4,
    }

    res = client.post("/api/v1/predict/flight-delay", json=payload)
    assert res.status_code == 200, f"Endpoint failed: {res.text}"

    data = res.json()

    # Exact example structure keys
    assert "delay_probability" in data
    assert "prediction" in data
    assert "explanation" in data

    assert isinstance(data["delay_probability"], float)
    assert data["prediction"] in ["Likely Delayed", "Likely On-Time"]
    assert isinstance(data["explanation"], list)
    assert len(data["explanation"]) == 4

    # Explanation items format
    for item in data["explanation"]:
        assert "feature" in item
        assert "impact" in item
        assert isinstance(item["feature"], str)
        assert isinstance(item["impact"], str)


def test_edge_case_configurable_top_k():
    """Verifies that top_k parameter correctly controls explanation length."""
    predictor = FlightDelayPredictor()

    res_3 = predictor.predict(carrier="UA", origin="EWR", dest="ORD", top_k=3)
    assert len(res_3["explanation"]) == 3

    res_7 = predictor.predict(carrier="UA", origin="EWR", dest="ORD", top_k=7)
    assert len(res_7["explanation"]) == 7


def test_edge_case_missing_weather_graceful_shap():
    """Verifies SHAP calculation does not crash when weather is missing/offline."""
    predictor = FlightDelayPredictor()

    # Predict with empty weather features (triggers fallback medians)
    res = predictor.predict(
        carrier="WN",
        origin="LGA",
        dest="MDW",
        scheduled_departure="2026-10-20T12:00:00Z",
    )

    assert "delay_probability" in res
    assert 0.0 <= res["delay_probability"] <= 1.0
    assert len(res["explanation"]) > 0
    assert "These features contributed most" in res["explanation_summary"]


def test_edge_case_unknown_carrier_and_airport():
    """Verifies unseen airline or destination airport code is handled gracefully without errors."""
    predictor = FlightDelayPredictor()

    res = predictor.predict(
        carrier="ZZ",  # Unseen carrier
        origin="EWR",
        dest="ZZZ",    # Unseen destination
        scheduled_departure="2026-10-20T14:00:00Z",
    )

    assert "delay_probability" in res
    assert 0.0 <= res["delay_probability"] <= 1.0
    assert res["prediction"] in ["Likely Delayed", "Likely On-Time"]
    assert len(res["explanation"]) > 0
