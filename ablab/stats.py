"""The usual fixed-horizon analysis, from running totals (notebook 02).

Shown on the page as the 'usual interval', only valid if you look once.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

Z95 = 1.959963984540054


def diff_in_proportions(s_t, n_t, s_c, n_c):
    """Estimate, unpooled standard error and z statistic. Works on scalars or arrays."""
    s_t, n_t, s_c, n_c = (np.asarray(x, dtype=float) for x in (s_t, n_t, s_c, n_c))
    p_t, p_c = s_t / n_t, s_c / n_c
    d = p_t - p_c
    se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(se > 0, d / se, 0.0)
    return d, se, z


def naive_interval(s_t, n_t, s_c, n_c, z_crit: float = Z95):
    d, se, _ = diff_in_proportions(s_t, n_t, s_c, n_c)
    return d - z_crit * se, d + z_crit * se


def naive_p_value(s_t, n_t, s_c, n_c):
    _, _, z = diff_in_proportions(s_t, n_t, s_c, n_c)
    return 2 * norm.sf(np.abs(z))


def diff_in_means(n_t, s_t, ss_t, n_c, s_c, ss_c):
    """Difference in means and Welch standard error from running sums (count, sum, sum of squares).

    Used for the CUPAC-adjusted outcome and the guardrail's value per player.
    """
    n_t, s_t, ss_t, n_c, s_c, ss_c = (np.asarray(v, dtype=float) for v in (n_t, s_t, ss_t, n_c, s_c, ss_c))
    m_t, m_c = s_t / n_t, s_c / n_c
    v_t = (ss_t - n_t * m_t**2) / (n_t - 1)
    v_c = (ss_c - n_c * m_c**2) / (n_c - 1)
    d = m_t - m_c
    se = np.sqrt(v_t / n_t + v_c / n_c)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(se > 0, d / se, 0.0)
    return d, se, z
