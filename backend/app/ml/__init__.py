"""
AeroAI Machine Learning Subsystem.
Provides flight delay predictive modeling, feature engineering, and inference services.
"""

from app.ml.predictor import FlightDelayPredictor, delay_predictor

__all__ = ["FlightDelayPredictor", "delay_predictor"]
