"""
Reproducible Preprocessing & Feature Pipeline for Pre-Flight Delay Prediction.

Guarantees zero data leakage by:
1. Transforming only features known prior to departure.
2. Integrating weather features with graceful fallback imputation when weather is absent.
3. Learning categorical target delay rates strictly from the training partition.
4. Applying cyclical trigonometric transformations for temporal periodicity.
5. Standard scaling continuous numerical indicators.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class FlightFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Leakage-free feature engineering and encoding pipeline for flight delay prediction,
    seamlessly supporting both weather-enriched and schedule-only inputs.
    """

    def __init__(self):
        self.carrier_rates_: Dict[str, float] = {}
        self.dest_rates_: Dict[str, float] = {}
        self.origin_rates_: Dict[str, float] = {}
        self.hour_rates_: Dict[str, float] = {}
        self.global_rate_: float = 0.2447
        self.cat_cols: List[str] = ["carrier", "origin"]
        self.num_cols: List[str] = [
            "month",
            "day",
            "day_of_week",
            "is_weekend",
            "sched_dep_hour",
            "sched_dep_min",
            "sin_hour",
            "cos_hour",
            "sin_month",
            "cos_month",
            "sin_dow",
            "cos_dow",
            "distance",
            "sched_elapsed_min",
            "carrier_delay_rate",
            "dest_delay_rate",
            "origin_delay_rate",
            "hour_delay_rate",
        ]
        self.weather_cols: List[str] = [
            "temp",
            "dewp",
            "humid",
            "wind_speed",
            "precip",
            "pressure",
            "visib",
            "is_fog",
            "is_high_wind",
            "is_freezing",
            "has_precip",
        ]
        # Empirical training partition medians for graceful zero-crash imputation
        self.weather_defaults_: Dict[str, float] = {
            "temp": 55.4,
            "dewp": 41.8,
            "humid": 60.9,
            "wind_speed": 10.3,
            "precip": 0.0,
            "pressure": 1017.9,
            "visib": 10.0,
            "is_fog": 0.0,
            "is_high_wind": 0.0,
            "is_freezing": 0.0,
            "has_precip": 0.0,
        }
        self.all_num_cols: List[str] = self.num_cols + self.weather_cols
        self.column_transformer_: Optional[ColumnTransformer] = None
        self.feature_names_: List[str] = []

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derives pre-flight mathematical, cyclical, historical, and weather indicators."""
        d = df.copy()

        # Date & Day of week
        if "day_of_week" not in d.columns:
            if "date" in d.columns:
                d["day_of_week"] = pd.to_datetime(d["date"]).dt.dayofweek
            elif "year" in d.columns and "month" in d.columns and "day" in d.columns:
                date = pd.to_datetime(
                    d["year"].astype(str)
                    + "-"
                    + d["month"].astype(str).str.zfill(2)
                    + "-"
                    + d["day"].astype(str).str.zfill(2)
                )
                d["day_of_week"] = date.dt.dayofweek
            else:
                d["day_of_week"] = 2  # Wednesday default

        if "is_weekend" not in d.columns:
            d["is_weekend"] = d["day_of_week"].isin([5, 6]).astype(int)

        if "sched_dep_hour" not in d.columns:
            if "hour" in d.columns:
                d["sched_dep_hour"] = d["hour"].astype(int)
            elif "sched_dep_time" in d.columns:
                d["sched_dep_hour"] = (d["sched_dep_time"] // 100).astype(int)
            else:
                d["sched_dep_hour"] = 12

        if "sched_dep_min" not in d.columns:
            if "minute" in d.columns:
                d["sched_dep_min"] = d["minute"].astype(int)
            elif "sched_dep_time" in d.columns:
                d["sched_dep_min"] = (d["sched_dep_time"] % 100).astype(int)
            else:
                d["sched_dep_min"] = 0

        if "sched_elapsed_min" not in d.columns:
            if "sched_arr_time" in d.columns and "sched_dep_time" in d.columns:
                arr_h = d["sched_arr_time"] // 100
                arr_m = d["sched_arr_time"] % 100
                dep_h = d["sched_dep_time"] // 100
                dep_m = d["sched_dep_time"] % 100
                elapsed = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
                d["sched_elapsed_min"] = np.where(elapsed < 0, elapsed + 1440, elapsed).astype(float)
            elif "distance" in d.columns:
                d["sched_elapsed_min"] = (d["distance"] / 8.0 + 35.0).astype(float)
            else:
                d["sched_elapsed_min"] = 130.0

        if "distance" not in d.columns:
            d["distance"] = 1000.0

        if "month" not in d.columns:
            d["month"] = 6
        if "day" not in d.columns:
            d["day"] = 15

        # Cyclical trigonometric transforms
        d["sin_hour"] = np.sin(2 * np.pi * d["sched_dep_hour"] / 24.0)
        d["cos_hour"] = np.cos(2 * np.pi * d["sched_dep_hour"] / 24.0)
        d["sin_month"] = np.sin(2 * np.pi * d["month"] / 12.0)
        d["cos_month"] = np.cos(2 * np.pi * d["month"] / 12.0)
        d["sin_dow"] = np.sin(2 * np.pi * d["day_of_week"] / 7.0)
        d["cos_dow"] = np.cos(2 * np.pi * d["day_of_week"] / 7.0)

        # Historical delay rates strictly from training partition
        d["carrier_delay_rate"] = (
            d["carrier"].map(self.carrier_rates_).fillna(self.global_rate_).astype(float)
        )
        d["dest_delay_rate"] = (
            d["dest"].map(self.dest_rates_).fillna(self.global_rate_).astype(float)
        )
        d["origin_delay_rate"] = (
            d["origin"].map(self.origin_rates_).fillna(self.global_rate_).astype(float)
        )
        d["hour_delay_rate"] = (
            d["sched_dep_hour"].map(self.hour_rates_).fillna(self.global_rate_).astype(float)
        )

        # Weather features with graceful imputation if missing
        for col in self.weather_cols:
            if col in d.columns:
                d[col] = d[col].fillna(self.weather_defaults_[col]).astype(float)
            else:
                d[col] = float(self.weather_defaults_[col])

        # Recalculate severe operational indicators if base weather values provided
        if "visib" in d.columns and ("is_fog" not in df.columns or df["is_fog"].isna().any()):
            d["is_fog"] = (d["visib"] < 3.0).astype(float)
        if "wind_speed" in d.columns and ("is_high_wind" not in df.columns or df["is_high_wind"].isna().any()):
            d["is_high_wind"] = (d["wind_speed"] >= 25.0).astype(float)
        if "temp" in d.columns and ("is_freezing" not in df.columns or df["is_freezing"].isna().any()):
            d["is_freezing"] = (d["temp"] <= 32.0).astype(float)
        if "precip" in d.columns and ("has_precip" not in df.columns or df["has_precip"].isna().any()):
            d["has_precip"] = (d["precip"] > 0.0).astype(float)

        return d

    def fit(self, X: pd.DataFrame, y: Any):
        """Fits target rates and weather medians on training partition."""
        df = X.copy()
        target_series = y.values if hasattr(y, "values") else np.array(y)
        df["_target"] = target_series

        self.global_rate_ = float(df["_target"].mean())
        self.carrier_rates_ = df.groupby("carrier")["_target"].mean().to_dict()
        self.dest_rates_ = df.groupby("dest")["_target"].mean().to_dict()
        self.origin_rates_ = df.groupby("origin")["_target"].mean().to_dict()
        self.hour_rates_ = df.groupby("sched_dep_hour")["_target"].mean().to_dict()

        # Learn training partition medians for weather features
        for col in self.weather_cols:
            if col in X.columns and not X[col].dropna().empty:
                self.weather_defaults_[col] = float(X[col].median())

        self.all_num_cols = self.num_cols + self.weather_cols
        eng_df = self._engineer_features(X)

        self.column_transformer_ = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.cat_cols),
                ("num", StandardScaler(), self.all_num_cols),
            ]
        )
        self.column_transformer_.fit(eng_df[self.cat_cols + self.all_num_cols])

        # Extract output feature names
        cat_encoder = self.column_transformer_.named_transformers_["cat"]
        cat_names = list(cat_encoder.get_feature_names_out(self.cat_cols))
        self.feature_names_ = cat_names + self.all_num_cols

        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms input DataFrame into model-ready numpy feature matrix."""
        if self.column_transformer_ is None:
            raise RuntimeError("FlightFeatureTransformer must be fitted before transforming.")

        eng_df = self._engineer_features(X)
        return self.column_transformer_.transform(eng_df[self.cat_cols + self.all_num_cols])

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        return list(self.feature_names_)
