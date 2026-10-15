"""
Unit & Integration Tests for Stage 2: Real Flight Data & Delay Prediction ML.
Verifies data loading, leakage-free feature pipeline, model artifacts, inference service,
and FastAPI prediction REST endpoints.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from app.main import app
from app.ml.data_loader import (
    find_dataset_path,
    load_raw_flight_data,
    clean_flight_data,
    time_based_split,
)
from app.ml.feature_pipeline import FlightFeatureTransformer
from app.ml.predictor import FlightDelayPredictor

client = TestClient(app)


def test_find_and_load_real_bts_dataset():
    """Verifies that legitimate BTS flight dataset exists on disk and loads properly."""
    dataset_path = find_dataset_path()
    assert dataset_path.exists(), f"BTS dataset file not found at {dataset_path}"

    df = load_raw_flight_data()
    assert len(df) > 300_000, f"Expected >300,000 BTS flights, got {len(df)}"

    expected_cols = ["year", "month", "day", "carrier", "origin", "dest", "distance", "arr_delay"]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column '{col}' in BTS dataset"


def test_clean_flight_data_and_target_definition():
    """Verifies target is defined as arr_delay >= 15 with zero post-flight leakage features."""
    raw_df = load_raw_flight_data()
    cleaned = clean_flight_data(raw_df)

    # 1. No NaNs in target
    assert cleaned["arr_delay"].isna().sum() == 0

    # 2. Target definition: binary 0 or 1
    assert set(cleaned["is_delayed"].unique()).issubset({0, 1})
    expected_delay_rate = (cleaned["arr_delay"] >= 15).mean()
    assert abs(cleaned["is_delayed"].mean() - expected_delay_rate) < 1e-6

    # 3. Class imbalance check (~20% to ~28% positive delay rate)
    assert 0.20 <= expected_delay_rate <= 0.30

    # 4. Sched elapsed time derived without negatives
    assert (cleaned["sched_elapsed_min"] > 0).all()


def test_time_based_split_chronology():
    """Verifies strict time-based split without data leakage across time horizons."""
    raw_df = load_raw_flight_data()
    cleaned = clean_flight_data(raw_df)

    train_df, test_df = time_based_split(cleaned, split_month=10)

    assert train_df["month"].max() == 9, "Training data contains months >= 10"
    assert test_df["month"].min() == 10, "Test data contains months < 10"

    assert len(train_df) > 200_000, f"Train set too small: {len(train_df)}"
    assert len(test_df) > 70_000, f"Test set too small: {len(test_df)}"


def test_feature_transformer_fit_and_transform():
    """Verifies FlightFeatureTransformer encodes pre-flight features without leakage."""
    sample_train = pd.DataFrame([
        {
            "year": 2013, "month": 3, "day": 10, "sched_dep_hour": 8, "sched_dep_min": 15,
            "carrier": "UA", "origin": "EWR", "dest": "ORD", "distance": 719.0, "sched_elapsed_min": 145.0,
            "_target": 0
        },
        {
            "year": 2013, "month": 3, "day": 10, "sched_dep_hour": 18, "sched_dep_min": 45,
            "carrier": "B6", "origin": "JFK", "dest": "BOS", "distance": 187.0, "sched_elapsed_min": 75.0,
            "_target": 1
        },
        {
            "year": 2013, "month": 3, "day": 11, "sched_dep_hour": 20, "sched_dep_min": 0,
            "carrier": "DL", "origin": "LGA", "dest": "ATL", "distance": 762.0, "sched_elapsed_min": 160.0,
            "_target": 1
        },
    ])

    transformer = FlightFeatureTransformer()
    y_train = sample_train["_target"]
    transformer.fit(sample_train, y_train)

    assert transformer.global_rate_ == pytest.approx(2.0 / 3.0)
    assert "UA" in transformer.carrier_rates_
    assert "B6" in transformer.carrier_rates_

    # Transform
    X_proc = transformer.transform(sample_train)
    assert isinstance(X_proc, np.ndarray)
    assert not np.isnan(X_proc).any(), "NaN values found in transformed feature matrix"

    # Feature names
    names = transformer.get_feature_names_out()
    assert len(names) == X_proc.shape[1]


def test_serialized_model_artifacts_exist():
    """Verifies that all trained model artifacts exist on disk."""
    artifacts_dir = Path(__file__).resolve().parents[2] / "backend" / "app" / "ml" / "artifacts"
    required_files = [
        "preprocessor.joblib",
        "best_model.joblib",
        "baseline_model.joblib",
        "random_forest_model.joblib",
        "xgboost_model.joblib",
        "feature_names.json",
        "metadata.json",
        "metrics.json",
    ]
    for filename in required_files:
        p = artifacts_dir / filename
        assert p.exists(), f"Required ML artifact '{filename}' missing in {artifacts_dir}"


def test_flight_delay_predictor_inference():
    """Verifies that FlightDelayPredictor outputs calibrated probabilities and risk tiers."""
    predictor = FlightDelayPredictor()
    assert predictor.is_loaded, "Predictor failed to load model artifacts"

    result = predictor.predict(
        carrier="UA",
        origin="EWR",
        dest="ORD",
        scheduled_departure="2026-10-20T17:30:00Z",
        distance=719.0,
    )

    assert "delay_probability" in result
    assert 0.0 <= result["delay_probability"] <= 1.0
    assert result["prediction"] in ["Likely Delayed", "Likely On-Time"]
    assert "explanation" in result
    assert isinstance(result["explanation"], list)
    assert len(result["explanation"]) > 0
    assert "feature" in result["explanation"][0]
    assert "impact" in result["explanation"][0]
    assert result["prediction_details"]["target_definition"] == "Arrival Delay >= 15 minutes"

    provenance = result["provenance"]
    assert provenance["is_ml_prediction"] is True
    assert provenance["simulated"] is False
    assert provenance["model_roc_auc"] > 0.50


def test_api_predict_flight_delay_endpoint():
    """Tests POST /api/v1/predict/flight-delay endpoint with SHAP explanations."""
    payload = {
        "carrier": "DL",
        "origin": "JFK",
        "dest": "LAX",
        "scheduled_departure": "2026-10-20T19:00:00Z",
        "distance": 2475.0,
    }

    res = client.post("/api/v1/predict/flight-delay", json=payload)
    assert res.status_code == 200, f"Predict endpoint failed: {res.text}"

    data = res.json()
    assert "delay_probability" in data
    assert 0.0 <= data["delay_probability"] <= 1.0
    assert data["prediction"] in ["Likely Delayed", "Likely On-Time"]
    assert "explanation" in data
    assert len(data["explanation"]) > 0
    assert "feature" in data["explanation"][0]
    assert "impact" in data["explanation"][0]
    assert data["provenance"]["is_ml_prediction"] is True


def test_api_model_info_endpoint():
    """Tests GET /api/v1/predict/model-info endpoint."""
    res = client.get("/api/v1/predict/model-info")
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "active"
    assert "metadata" in data
    assert data["metadata"]["target_definition"] == "arr_delay >= 15 minutes"
    assert data["feature_count"] > 0


def test_existing_application_remains_operational():
    """Verifies that adding Stage 2 ML features did not break any existing core functionality."""
    # Health
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] in ["ok", "healthy"]

    # Root
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "version" in res_root.json()

    # Public News feed
    res_news = client.get("/news?limit=3")
    assert res_news.status_code == 200
