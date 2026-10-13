"""The known-truth simulator (notebook 01), driven by config/simulator.toml.

Random draws happen in the same order as in notebook 01, so the same seed gives the same players.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

from ablab.assign import assignment_us, is_treated
from ablab.config import load

STREAMS = ("arrivals", "covariates", "outcomes", "journey")


def hour_shape(cfg: dict | None = None) -> np.ndarray:
    """Relative sign-ups by hour of day, mean 1."""
    hs = (cfg or load())["arrivals"]["hour_shape"]
    h = np.arange(24)
    night = hs["night_level"] + hs["night_amp"] * np.cos(2 * np.pi * (h - hs["night_peak_hour"]) / 24)
    s = hs["night_weight"] * night
    for height, centre, width in hs["bumps"]:
        s = s + height * np.exp(-((h - centre) / width) ** 2)
    return s / s.mean()


def day_shape(cfg: dict | None = None) -> np.ndarray:
    w = np.array((cfg or load())["arrivals"]["weekday_shape"])
    return w / w.mean()


def streams(seed: int) -> dict[str, np.random.Generator]:
    """One independent generator per part of the model."""
    return dict(zip(STREAMS, (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(len(STREAMS)))))


def draw_arrivals(rng: np.random.Generator, cfg: dict | None = None):
    cfg = cfg or load()
    hours = np.arange(cfg["experiment"]["days"] * 24)
    lam = cfg["arrivals"]["per_hour"] * hour_shape(cfg)[hours % 24] * day_shape(cfg)[(hours // 24) % 7]
    return hours, lam, rng.poisson(lam)


def draw_covariates(signup_hour: np.ndarray, rng: np.random.Generator, cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or load()
    c, n = cfg["covariates"], len(signup_hour)
    tier = rng.choice(3, size=n, p=c["tier"]["p"])
    device = np.where(rng.random(n) < np.array(c["device"]["p_iphone_by_tier"])[tier], 0, 1)
    channel = rng.choice(3, size=n, p=c["channel"]["p"])
    hod = signup_hour % 24
    evening = (hod >= c["evening_hours"][0]) & (hod < c["evening_hours"][1])
    u = rng.normal(size=n)  # latent engagement, never observed by an analyst
    sg = cfg["signals"]
    games = rng.poisson(np.exp(sg["games_30d"]["log_mean"] + sg["games_30d"]["loading"] * u))
    k = sg["click_to_install_s"]
    click = np.exp(k["log_median"] - k["loading"] * u + rng.normal(0, k["noise_sd"], n))
    ps = sg["partner_score"]
    has_score = channel == c["channel"]["levels"].index(ps["channel"])
    score = np.where(has_score, expit(ps["loading"] * u + rng.normal(0, ps["noise_sd"], n)), np.nan)
    return pd.DataFrame({
        "signup_hour": signup_hour, "hour_of_day": hod, "weekday": (signup_hour // 24) % 7,
        "tier": tier, "device": device, "channel": channel, "evening": evening,
        "engagement": u, "games_30d": games, "click_to_install_s": click, "partner_score": score,
    })


def linear_predictor(cov: pd.DataFrame, cfg: dict | None = None) -> np.ndarray:
    """Log-odds of activating in control, without the intercept."""
    b = (cfg or load())["baseline_logit"]
    return (np.array(b["tier"])[cov.tier] + np.array(b["device"])[cov.device]
            + np.array(b["channel"])[cov.channel] + b["evening"] * cov.evening + b["engagement"] * cov.engagement)


def raw_multiplier(cov: pd.DataFrame, cfg: dict | None = None) -> np.ndarray:
    m = (cfg or load())["lift_multiplier"]
    return np.array(m["tier"])[cov.tier] * np.array(m["channel"])[cov.channel]


def calibrate(cfg: dict | None = None, n_ref: int = 400_000, seed: int = 1) -> tuple[float, float]:
    """Intercept giving the target baseline, and the mean lift multiplier, on a reference population."""
    cfg = cfg or load()
    rng = np.random.default_rng(seed)
    weights = np.outer(day_shape(cfg), hour_shape(cfg)).ravel() / (24 * 7)
    ref = draw_covariates(rng.choice(24 * 7, size=n_ref, p=weights), rng, cfg)
    eta = linear_predictor(ref, cfg)
    b0 = brentq(lambda b: expit(b + eta).mean() - cfg["experiment"]["baseline_rate"], -6, 6)
    return b0, float(raw_multiplier(ref, cfg).mean())


def simulate(lift: float, seed: int, cfg: dict | None = None,
             intercept: float | None = None, multiplier_mean: float | None = None):
    """Players over the experiment, with a true average lift of `lift` (probability points).

    Returns (players DataFrame, (hours, expected arrivals per hour, arrivals per hour)).
    """
    cfg = cfg or load()
    intercept = cfg["calibration"]["intercept"] if intercept is None else intercept
    multiplier_mean = cfg["calibration"]["multiplier_mean"] if multiplier_mean is None else multiplier_mean
    delay = cfg["plan"]["outcome_delay_h"]
    rng = streams(seed)
    hours, lam, counts = draw_arrivals(rng["arrivals"], cfg)
    df = draw_covariates(np.repeat(hours, counts), rng["covariates"], cfg)
    n = len(df)
    df.insert(0, "player_id", [f"Q{i:07d}" for i in range(n)])

    df["p0"] = expit(intercept + linear_predictor(df, cfg))
    df["tau"] = lift * raw_multiplier(df, cfg) / multiplier_mean
    df["p1"] = np.clip(df.p0 + df.tau, 0, 1)
    df["u"] = assignment_us(df.player_id, cfg["experiment"]["key"])
    df["treated"] = is_treated(df.u)
    df["activated"] = rng["outcomes"].random(n) < np.where(df.treated, df.p1, df.p0)
    df["analysed_at_hour"] = df.signup_hour + delay

    # journey: player story only
    j, r = cfg["journey"], rng["journey"]
    started = df.activated | (r.random(n) < j["p_start_if_not_activated"])
    t_start_h = r.lognormal(np.log(j["start_median_min"]), j["start_sigma"], n) / 60
    med = j["milestone_median_h"] * np.where(df.treated, j["treatment_speedup"], 1.0)
    t_ms = r.lognormal(np.log(med), j["milestone_sigma"])
    bad = (df.activated & (t_start_h + t_ms >= delay)).to_numpy()
    while bad.any():  # completions must land inside the window
        # a start drawn after the window (about 1 player in 50 million) can never fit: redraw the start too
        late_start = bad & (t_start_h >= delay - 1)
        if late_start.any():
            t_start_h[late_start] = r.lognormal(np.log(j["start_median_min"]), j["start_sigma"], late_start.sum()) / 60
        t_ms[bad] = r.lognormal(np.log(med[bad]), j["milestone_sigma"])
        bad = (df.activated & (t_start_h + t_ms >= delay)).to_numpy()
    late = ~df.activated & started & (r.random(n) < j["p_late_finisher"])
    df["started"] = started
    df["hours_to_start"] = np.where(started, t_start_h, np.nan)
    df["hours_to_milestone"] = np.where(df.activated, t_start_h + t_ms,
                                        np.where(late, delay + r.exponential(24, n), np.nan))
    return df, (hours, lam, counts)


def simulate_counts(lift: float, rng: np.random.Generator, runs: int, looks: int, batch: float,
                    base: float = 0.22) -> dict[str, np.ndarray]:
    """Fast aggregate simulator for validity studies (notebooks 02-03).

    Players are independent, so with segments averaged out each one activates with probability
    base (control) or base + lift (treatment). Returns running totals per look, shape (runs, looks).
    """
    n = rng.poisson(batch, size=(runs, looks))
    n_t = rng.binomial(n, 0.5)
    n_c = n - n_t
    return {"s_t": rng.binomial(n_t, base + lift).cumsum(1), "n_t": n_t.cumsum(1),
            "s_c": rng.binomial(n_c, base).cumsum(1), "n_c": n_c.cumsum(1)}
