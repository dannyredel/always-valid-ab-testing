"""CUPAC (notebook 06): a logistic model of activation from pre-sign-up signals, trained on an earlier
cohort, used as the covariate of a CUPED adjustment with theta and mu fixed outside the experiment.

The model is a list of weights (config/cupac.json), so the browser applies it identically.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

CUPAC_PATH = Path(__file__).resolve().parent.parent / "config" / "cupac.json"

# Fixed column order shared with web/src/lib/engine/cupac.ts
COLUMNS = ["evening", "log_games", "log_click", "partner_score", "has_score",
           "tier_1", "tier_2", "device_1", "channel_1", "channel_2"]


def design(players: pd.DataFrame) -> np.ndarray:
    """Feature matrix in COLUMNS order (categories one-hot, first level dropped)."""
    score = players.partner_score
    return np.column_stack([
        players.evening.astype(float),
        np.log1p(players.games_30d),
        np.log(players.click_to_install_s),
        score.fillna(0.0),
        score.notna().astype(float),
        (players.tier == 1).astype(float), (players.tier == 2).astype(float),
        (players.device == 1).astype(float),
        (players.channel == 1).astype(float), (players.channel == 2).astype(float),
    ])


def train(cohort: pd.DataFrame) -> dict:
    """Fit on the first week, fix theta and mu on the second (notebook 06)."""
    from sklearn.linear_model import LogisticRegression

    first, second = cohort[cohort.signup_hour < 7 * 24], cohort[cohort.signup_hour >= 7 * 24]
    model = LogisticRegression(max_iter=1000).fit(design(first), first.activated)
    m = {"columns": COLUMNS, "intercept": float(model.intercept_[0]), "weights": [float(w) for w in model.coef_[0]]}
    x = score(second, m)
    y = second.activated.to_numpy(float)
    m["theta"] = float(np.cov(y, x)[0, 1] / x.var(ddof=1))
    m["mu"] = float(x.mean())
    m["r2_holdout"] = float(np.corrcoef(y, x)[0, 1] ** 2)
    return m


def score(players: pd.DataFrame, m: dict) -> np.ndarray:
    """Predicted probability of activating under standard rewards."""
    return expit(m["intercept"] + design(players) @ np.asarray(m["weights"]))


def adjusted(y, x, m: dict):
    """CUPED-adjusted outcome."""
    return np.asarray(y, float) - m["theta"] * (np.asarray(x) - m["mu"])


def load(path: Path | str = CUPAC_PATH) -> dict:
    return json.loads(Path(path).read_text())
