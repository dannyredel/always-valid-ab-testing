"""Segment monitoring (notebook 05): 'is any group being harmed?'

Each pre-chosen segment level gets the always-valid interval at alpha / K (Bonferroni over the K levels
shown), tuned to the segment's expected share of the planned sample. A segment is 'harmed' when its
whole interval is below zero. Trustworthy when it fires; it only catches large harms (notebook 05).
"""

from __future__ import annotations

import numpy as np

from ablab.sequential import cs_multiplier, rho2_for
from ablab.stats import diff_in_proportions

MIN_PLAYERS = 300  # per segment, before its interval is shown


def levels(cfg: dict) -> list[tuple[str, str, float]]:
    """(dimension, level, expected share) for every segment level, in page order."""
    c = cfg["covariates"]
    tier_p = np.array(c["tier"]["p"])
    iphone = float(tier_p @ np.array(c["device"]["p_iphone_by_tier"]))
    out = [("Country tier", lvl, float(p)) for lvl, p in zip(c["tier"]["levels"], tier_p)]
    out += [("Device", c["device"]["levels"][0], iphone), ("Device", c["device"]["levels"][1], 1 - iphone)]
    out += [("Channel", lvl, float(p)) for lvl, p in zip(c["channel"]["levels"], c["channel"]["p"])]
    return out


def segment_interval(s_t, n_t, s_c, n_c, share: float, k: int, alpha: float, n_star: float):
    """Always-valid interval for one segment's lift at this look (not yet intersected)."""
    d, se, _ = diff_in_proportions(s_t, n_t, s_c, n_c)
    a = alpha / k
    half = se * cs_multiplier(np.asarray(n_t) + np.asarray(n_c), rho2_for(n_star * share, a), a)
    return d - half, d + half
