"""Planning (notebook 04): break-even lift and sample sizes."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from ablab.sequential import cs_multiplier, rho2_for


def break_even_lift(p_c: float, p_reach_level10: float, bonus_usd: float, value_per_activation: float) -> float:
    """Lift at which the Starter Bonus pays for itself: Δ V = (p_C + Δ)(1 - q) b."""
    extra = (1 - p_reach_level10) * bonus_usd
    return p_c * extra / (value_per_activation - extra)


def fixed_horizon_n(p_c: float, lift: float, alpha: float = 0.05, power: float = 0.8,
                    variance_factor: float = 1.0) -> float:
    """Total players (both arms, 50/50) for a one-look two-sided test."""
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    v = p_c * (1 - p_c) + (p_c + lift) * (1 - p_c - lift)
    return 2 * (za + zb) ** 2 * v / lift**2 * variance_factor


def sequential_power(p_c: float, lift: float, n_max: int, rng: np.random.Generator, runs: int = 1_000,
                     batch_per_arm: int = 125, alpha: float = 0.05, min_n: float = 1_000,
                     variance_factor: float = 1.0) -> tuple[float, np.ndarray]:
    """Chance of 'ship' within n_max (interval tuned to n_max), and players at ship (NaN if none).

    Gaussian increments per batch; matches the exact binomial simulation of notebook 03.
    """
    looks = int(np.ceil(n_max / (2 * batch_per_arm)))
    k = np.arange(1, looks + 1)
    n = k * 2 * batch_per_arm
    v = (p_c * (1 - p_c) + (p_c + lift) * (1 - p_c - lift)) * variance_factor
    shocks = rng.standard_normal((runs, looks)).cumsum(1)
    d = lift + shocks * np.sqrt(v * batch_per_arm) / (batch_per_arm * k)
    se = np.sqrt(v / (batch_per_arm * k))
    lo = d - cs_multiplier(n, rho2_for(n_max, alpha), alpha) * se
    hit = (lo > 0) & (n >= min_n) & (n <= n_max)
    shipped = hit.any(1)
    return shipped.mean(), np.where(shipped, n[hit.argmax(1)], np.nan)
