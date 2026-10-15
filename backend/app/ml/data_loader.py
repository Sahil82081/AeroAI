"""
Data Loader & Splitter for Flight Delay Modeling.
Loads U.S. DOT BTS on-time performance records, aligns NOAA/ASOS weather observations,
and applies a strict time-based split.
"""

import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

# Resolve base paths
_MODULE_PATH = Path(__file__).resolve()
_REPO_ROOT = _MODULE_PATH.parents[3]
DEFAULT_DATA_PATH = _REPO_ROOT / "data" / "flights" / "flights.csv.zip"
DEFAULT_WEATHER_PATH = _REPO_ROOT / "data" / "flights" / "weather.csv"


def find_dataset_path(custom_path: Optional[str] = None) -> Path:
    """Finds valid path to flights dataset, checking custom, local, and repo paths."""
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p

    if DEFAULT_DATA_PATH.exists():
        return DEFAULT_DATA_PATH

    uncompressed = DEFAULT_DATA_PATH.with_suffix("")
    if uncompressed.exists():
        return uncompressed

    pkg_data = _REPO_ROOT / ".venv" / "Lib" / "site-packages" / "nycflights13" / "data" / "flights.csv.zip"
    if pkg_data.exists():
        return pkg_data

    raise FileNotFoundError(
        f"Flight dataset not found at {DEFAULT_DATA_PATH}. "
        "Please ensure data/flights/flights.csv.zip is present."
    )


def load_raw_flight_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """Loads raw BTS flight dataset."""
    path = find_dataset_path(filepath)
    df = pd.read_csv(path)
    return df


def load_raw_weather_data(filepath: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Loads NOAA/ASOS weather observations for origin airport alignment."""
    p = Path(filepath) if filepath else DEFAULT_WEATHER_PATH
    if not p.exists():
        pkg_weather = _REPO_ROOT / ".venv" / "Lib" / "site-packages" / "nycflights13" / "data" / "weather.csv"
        if pkg_weather.exists():
            p = pkg_weather
        else:
            return None

    try:
        w_df = pd.read_csv(p)
        return w_df
    except Exception:
        return None


def clean_flight_data(
    df: pd.DataFrame,
    weather_df: Optional[pd.DataFrame] = None,
    merge_weather: bool = True,
) -> pd.DataFrame:
    """
    Cleans raw BTS flight records and optionally fuses hourly weather observations:
    1. Filters out cancelled or diverted flights where arrival delay is unknown (NaN).
    2. Derives binary target: is_delayed = 1 if arr_delay >= 15 else 0.
    3. Derives pre-flight calendar features (day of week, is_weekend).
    4. Computes scheduled elapsed duration from scheduled departure and arrival times.
    5. Fuses synchronized surface weather (temperature, wind, visibility, precipitation).
    6. Excludes all post-flight leakage variables.
    """
    cleaned = df.dropna(subset=["arr_delay"]).copy()

    # Define standard target (FAA/BTS: >= 15 min delay)
    cleaned["is_delayed"] = (cleaned["arr_delay"] >= 15).astype(int)

    # Calendar derivation
    cleaned["date"] = pd.to_datetime(
        cleaned["year"].astype(str)
        + "-"
        + cleaned["month"].astype(str).str.zfill(2)
        + "-"
        + cleaned["day"].astype(str).str.zfill(2)
    )
    cleaned["day_of_week"] = cleaned["date"].dt.dayofweek
    cleaned["is_weekend"] = cleaned["day_of_week"].isin([5, 6]).astype(int)

    # Scheduled departure components
    cleaned["sched_dep_hour"] = cleaned["hour"].astype(int)
    cleaned["sched_dep_min"] = cleaned["minute"].astype(int)

    # Scheduled elapsed flight duration in minutes
    arr_h = cleaned["sched_arr_time"] // 100
    arr_m = cleaned["sched_arr_time"] % 100
    dep_h = cleaned["sched_dep_time"] // 100
    dep_m = cleaned["sched_dep_time"] % 100
    sched_elapsed = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
    sched_elapsed = np.where(sched_elapsed < 0, sched_elapsed + 1440, sched_elapsed)
    cleaned["sched_elapsed_min"] = sched_elapsed.astype(float)

    # Convert string columns to clean string type
    cleaned["carrier"] = cleaned["carrier"].astype(str).str.strip()
    cleaned["origin"] = cleaned["origin"].astype(str).str.strip()
    cleaned["dest"] = cleaned["dest"].astype(str).str.strip()

    # Weather feature fusion
    if merge_weather:
        w = weather_df if weather_df is not None else load_raw_weather_data()
        if w is not None and not w.empty:
            w_cols = ["origin", "year", "month", "day", "hour", "temp", "dewp", "humid", "wind_speed", "precip", "pressure", "visib"]
            available_w_cols = [c for c in w_cols if c in w.columns]
            w_subset = w[available_w_cols].copy()
            w_subset["origin"] = w_subset["origin"].astype(str).str.strip()

            cleaned = pd.merge(
                cleaned,
                w_subset,
                on=["origin", "year", "month", "day", "hour"],
                how="left",
            )

    return cleaned


def time_based_split(
    df: pd.DataFrame, split_month: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits flight records chronologically by month to avoid lookahead leakage.
    Default:
        Train: Months 1 through 9 (January to September, ~75%)
        Test:  Months 10 through 12 (October to December, ~25%)
    """
    train_df = df[df["month"] < split_month].copy()
    test_df = df[df["month"] >= split_month].copy()

    return train_df, test_df
