"""Always-valid inference (notebook 03): normal-mixture confidence sequence and p-value.

Waudby-Smith et al. (2023), the method in GrowthBook's gbstats. Checked against gbstats in tests.
"""

from __future__ import annotations

import numpy as np


def rho2_for(n_star: float, alpha: float = 0.05) -> float:
    """Mixing variance that makes the interval tightest at n_star players (eq. 161)."""
    a = -2 * np.log(alpha)
    return (a + np.log(a + 1)) / n_star


def cs_multiplier(n, rho2: float, alpha: float = 0.05):
    """Replaces 1.96: half-width of the always-valid interval in standard errors."""
    t = np.asarray(n, dtype=float) * rho2
    return np.sqrt(2 * (t + 1) / t * np.log(np.sqrt(t + 1) / alpha))


def log_wealth(z, n, rho2: float):
    """log of the mixture martingale Λ_n (the bet against 'no effect')."""
    t = np.asarray(n, dtype=float) * rho2
    return t * np.asarray(z, dtype=float) ** 2 / (2 * (t + 1)) - 0.5 * np.log(t + 1)


def p_value_at_look(z, n, rho2: float):
    """1 / Λ_n at this look (what gbstats reports)."""
    return np.minimum(1.0, np.exp(-log_wealth(z, n, rho2)))


def always_valid_p(z, n, rho2: float, axis: int = -1):
    """Running minimum of 1/Λ over looks: never increases."""
    return np.minimum.accumulate(p_value_at_look(z, n, rho2), axis=axis)


def confidence_sequence(d, se, n, rho2: float, alpha: float = 0.05):
    """Interval at each look (not yet intersected)."""
    half = np.asarray(se) * cs_multiplier(n, rho2, alpha)
    return np.asarray(d) - half, np.asarray(d) + half


def running_intersection(lo, hi, n=None, min_n: float = 0, axis: int = -1):
    """Intersect with all earlier looks: same guarantee, and the interval only narrows.

    Looks with fewer than min_n players are left out of the intersection, so a misleadingly
    narrow interval from a tiny early sample is never carried forward.
    """
    lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
    if n is not None:
        early = np.asarray(n) < min_n
        lo, hi = np.where(early, -np.inf, lo), np.where(early, np.inf, hi)
    return np.maximum.accumulate(lo, axis=axis), np.minimum.accumulate(hi, axis=axis)


def verdict(lo: float, hi: float, n: float, min_n: float, max_n: float) -> str:
    """Decision rule from the brief, applied to the (intersected) interval."""
    if n >= min_n and lo > 0:
        return "ship"
    if n >= min_n and hi < 0:
        return "dont_ship"
    if n >= max_n:
        return "inconclusive"
    return "keep_collecting"
