"""Health checks from running counts: sample-ratio mismatch and covariate balance.

The page checks the split at every update, so it uses the always-valid SRM test of Lindon & Malek
(2022), as implemented in savvi. The χ² test is kept as the one-look reference.
"""

from __future__ import annotations

import numpy as np
from scipy.special import gammaln
from scipy.stats import chi2


def srm_chi2(n_c: int, n_t: int, share_t: float = 0.5) -> float:
    """p-value of Pearson's χ² test against the planned split. Valid for a single look only."""
    n = n_c + n_t
    expected = np.array([n * (1 - share_t), n * share_t])
    stat = (((np.array([n_c, n_t]) - expected) ** 2) / expected).sum()
    return float(chi2.sf(stat, df=1))


def srm_log_bayes_factor(n_c: int, n_t: int, share_t: float = 0.5, k: float = 100.0) -> float:
    """Log Bayes factor against the planned split: Dirichlet-multinomial mixture, prior k * theta_0.

    log BF = log B(alpha_0 + x) - log B(alpha_0) - sum x_i log theta_i, with B the multivariate beta.
    Equals log(odds) in savvi.multinomial.Multinomial (checked in tests).
    """
    theta = np.array([1 - share_t, share_t])
    x = np.array([n_c, n_t], dtype=float)
    a0 = k * theta

    def log_beta(a):
        return gammaln(a).sum() - gammaln(a.sum())

    return float(log_beta(a0 + x) - log_beta(a0) - (x * np.log(theta)).sum())


def srm_always_valid_p(n_c, n_t, share_t: float = 0.5, k: float = 100.0) -> np.ndarray:
    """Running minimum of 1/BF over looks (arrays of cumulative counts): safe to check at every update."""
    p = [min(1.0, float(np.exp(-srm_log_bayes_factor(c, t, share_t, k)))) for c, t in zip(n_c, n_t)]
    return np.minimum.accumulate(p)


def smd_from_counts(k_c: int, n_c: int, k_t: int, n_t: int) -> float:
    """Standardised mean difference of a 0/1 indicator from counts (same definition as causalml).

    Uses sample variances (ddof=1), as pandas does inside causalml.match.create_table_one.
    """
    p_c, p_t = k_c / n_c, k_t / n_t
    var_c = p_c * (1 - p_c) * n_c / (n_c - 1)
    var_t = p_t * (1 - p_t) * n_t / (n_t - 1)
    denom = np.sqrt(0.5 * (var_c + var_t))
    return 0.0 if denom == 0 else (p_t - p_c) / denom
