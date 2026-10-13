"""Numbers for the page's *Before the experiment* section (notebook 04, with the stored CUPAC model).

    python -m scripts.plan_page      -> web/public/plan.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ablab import cupac
from ablab.config import load
from ablab.power import break_even_lift, fixed_horizon_n, sequential_power

OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "plan.json"
SEED = 20261022


def main():
    cfg = load()
    plan, p_c = cfg["plan"], cfg["experiment"]["baseline_rate"]
    r2 = cupac.load()["r2_holdout"]
    f = 1 - r2
    be = break_even_lift(p_c, plan["p_reach_level10"], plan["bonus_usd"], plan["value_per_activation_usd"])
    rng = np.random.default_rng(SEED)
    lifts = [0.0, 0.005, 0.01, 0.015, be, 0.02, 0.025, 0.03, 0.04, 0.05]
    curve = []
    for lift in lifts:
        pw, n_at = sequential_power(p_c, lift, plan["max_players"], rng, runs=2_000, variance_factor=f,
                                    min_n=plan["min_players"])
        curve.append({"lift": lift, "power": float(pw),
                      "median_players": None if np.isnan(n_at).all() else float(np.nanmedian(n_at)),
                      "q25": None if np.isnan(n_at).all() else float(np.nanpercentile(n_at, 25)),
                      "q75": None if np.isnan(n_at).all() else float(np.nanpercentile(n_at, 75))})
    out = {
        "baseline": p_c, "alpha": plan["alpha"], "power_target": plan["power"], "break_even": be,
        "cupac_r2": r2, "max_players": plan["max_players"], "signups_per_hour": cfg["arrivals"]["per_hour"],
        "outcome_delay_h": plan["outcome_delay_h"],
        "fixed_horizon_n": {"unadjusted": fixed_horizon_n(p_c, be), "cupac": fixed_horizon_n(p_c, be, variance_factor=f)},
        "power_at_break_even": next(c["power"] for c in curve if c["lift"] == be),
        "economics": {"bonus_usd": plan["bonus_usd"], "p_reach_level10": plan["p_reach_level10"],
                      "value_per_activation_usd": plan["value_per_activation_usd"]},
        "curve": curve,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT.relative_to(OUT.parents[2])}: break-even +{be * 100:.2f} pts, power there {out['power_at_break_even']:.1%}, "
          f"fixed-horizon N {out['fixed_horizon_n']['cupac']:,.0f} (CUPAC)")


if __name__ == "__main__":
    main()
