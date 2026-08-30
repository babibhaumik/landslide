"""
Landslide risk scoring model.

Two layers:

1. A transparent RULE-BASED score (always available, no training data
   needed). It combines:
     - how much MORE rain than normal an area has received (excess is the
       key landslide trigger, not just total rainfall)
     - the area's static terrain susceptibility (see terrain_susceptibility.py)

2. An OPTIONAL trainable scikit-learn LogisticRegression classifier you
   can fit later if you get access to real historical landslide event
   labels (e.g. from GSI Bhukosh or NRSC's landslide inventory). Until
   that training data exists, the API automatically falls back to the
   rule-based score, so the app is fully functional either way.
"""

from dataclasses import dataclass
from typing import Optional
import pickle
import os

import numpy as np

from terrain_susceptibility import get_terrain_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pkl")


@dataclass
class RiskResult:
    region: str
    actual_mm: float
    normal_mm: float
    departure_pct: float
    terrain_score: float
    risk_score: float       # 0-100
    risk_level: str         # Low / Moderate / High / Very High
    source: str              # "rule_based" or "trained_model"


def _rainfall_excess_factor(departure_pct: float) -> float:
    """
    Convert rainfall departure (%) into a 0-1 'excess factor'.

    Landslide risk from rainfall isn't linear - it rises sharply once an
    area crosses into surplus rainfall territory, and heavy DEFICIT
    rainfall does not meaningfully reduce landslide risk below a floor
    (a small deficit can still follow a wet spell). This uses a simple
    smooth ramp:
      <= 0% departure   -> factor rises slowly from 0.05 to 0.35
      0% to 60% surplus -> factor rises from 0.35 to 1.0
      > 60% surplus     -> capped at 1.0
    """
    if departure_pct <= -60:
        return 0.05
    if departure_pct <= 0:
        # deficit: -60% -> 0.05, 0% -> 0.35
        return 0.05 + (departure_pct + 60) / 60 * 0.30
    if departure_pct >= 60:
        return 1.0
    # 0% -> 0.35, 60% -> 1.0
    return 0.35 + (departure_pct / 60) * 0.65


def score_region_rule_based(region: str, actual_mm: float, normal_mm: float,
                             state_for_terrain: Optional[str] = None) -> RiskResult:
    state_for_terrain = state_for_terrain or region
    departure_pct = ((actual_mm - normal_mm) / normal_mm * 100) if normal_mm else 0.0
    terrain = get_terrain_score(state_for_terrain)
    rain_factor = _rainfall_excess_factor(departure_pct)

    # Weighted blend: terrain matters as much as rainfall excess for
    # landslide initiation - this 55/45 split reflects that terrain is
    # the necessary precondition, rainfall is the trigger.
    combined = (0.45 * rain_factor) + (0.55 * terrain)
    risk_score = round(combined * 100, 1)

    if risk_score >= 70:
        level = "Very High"
    elif risk_score >= 50:
        level = "High"
    elif risk_score >= 30:
        level = "Moderate"
    else:
        level = "Low"

    return RiskResult(
        region=region,
        actual_mm=actual_mm,
        normal_mm=normal_mm,
        departure_pct=round(departure_pct, 1),
        terrain_score=terrain,
        risk_score=risk_score,
        risk_level=level,
        source="rule_based",
    )


def load_trained_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return None


def score_region(region: str, actual_mm: float, normal_mm: float,
                  state_for_terrain: Optional[str] = None) -> RiskResult:
    """
    Main entry point used by the API. Uses the trained model if one has
    been fit and saved to trained_model.pkl; otherwise falls back to the
    transparent rule-based score.
    """
    model = load_trained_model()
    if model is None:
        return score_region_rule_based(region, actual_mm, normal_mm, state_for_terrain)

    departure_pct = ((actual_mm - normal_mm) / normal_mm * 100) if normal_mm else 0.0
    terrain = get_terrain_score(state_for_terrain or region)
    X = np.array([[departure_pct, terrain]])
    proba = model.predict_proba(X)[0][1]  # probability of "landslide risk" class
    risk_score = round(proba * 100, 1)

    if risk_score >= 70:
        level = "Very High"
    elif risk_score >= 50:
        level = "High"
    elif risk_score >= 30:
        level = "Moderate"
    else:
        level = "Low"

    return RiskResult(
        region=region,
        actual_mm=actual_mm,
        normal_mm=normal_mm,
        departure_pct=round(departure_pct, 1),
        terrain_score=terrain,
        risk_score=risk_score,
        risk_level=level,
        source="trained_model",
    )


def train_model(training_rows, save=True):
    """
    Train a simple logistic regression on real historical data.

    training_rows: list of dicts, each with keys:
        departure_pct (float), terrain_score (float), had_landslide (0 or 1)

    Call this once you have real historical rainfall + landslide-occurrence
    records (e.g. matched against GSI/NRSC landslide inventories). Until
    then, the app keeps using the rule-based scorer above.
    """
    from sklearn.linear_model import LogisticRegression

    X = np.array([[r["departure_pct"], r["terrain_score"]] for r in training_rows])
    y = np.array([r["had_landslide"] for r in training_rows])

    model = LogisticRegression()
    model.fit(X, y)

    if save:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)

    return model
