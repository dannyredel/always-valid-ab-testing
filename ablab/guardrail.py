"""The guardrail (notebook 06): projected net value per player, and its traffic light.

Value per player: an activated player is worth V (lifetime net margin); in the Starter Bonus arm,
each activated player also costs the expected early payout c = bonus x (1 - share reaching level 10).
"""

from __future__ import annotations

import numpy as np


def extra_cost(plan: dict) -> float:
    return plan["bonus_usd"] * (1 - plan["p_reach_level10"])


def value(activated, treated, plan: dict):
    v = plan["value_per_activation_usd"]
    return np.asarray(activated, float) * np.where(np.asarray(treated), v - extra_cost(plan), v)


def light(lo: float, hi: float) -> str:
    """'red' (costs more than it brings), 'green' (pays), 'grey' (not clear yet)."""
    if hi < 0:
        return "red"
    if lo > 0:
        return "green"
    return "grey"


def final_verdict(lift_verdict: str, pays: str) -> str:
    """Decision rule (DECISIONS.md, 2026-10-12): ship when the lift is shown above zero and the
    guardrail is not red; a confirmed lift with a red guardrail becomes 'doesnt_pay'."""
    if lift_verdict == "ship" and pays == "red":
        return "doesnt_pay"
    return lift_verdict


def value_from_lift(lift, p_c: float, plan: dict):
    """Value per player, Starter Bonus minus standard ($), as an exact function of the lift:
    (V - c) * lift - c * p_C. Increasing in the lift, so an always-valid lift interval [lo, hi] maps to
    the value interval [value_from_lift(lo), value_from_lift(hi)] (p_C as a plug-in estimate).
    'Pays' (green) is then exactly 'the lift is shown above break-even'."""
    c = extra_cost(plan)
    return (plan["value_per_activation_usd"] - c) * np.asarray(lift, float) - c * p_c
