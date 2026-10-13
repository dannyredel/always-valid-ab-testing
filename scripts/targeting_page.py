"""Numbers for the page's *Ship it to whom?* section (notebook 08).

Reads the repeated experiments cached by notebook 08 (results/08_targeting.json) and recomputes the
simulator's truth on the same scoring population. Nothing is fitted here.

    python -m scripts.targeting_page      -> web/public/targeting.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ablab import cupac, guardrail
from ablab.config import load
from ablab.simulator import simulate

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "08_targeting.json"
OUT = ROOT / "web" / "public" / "targeting.json"
SEED = 20261022  # notebook 08
RULES = {"everyone": "true_all", "subgroups": "true_subgroups", "baseline_rule": "true_baseline_rule",
         "forest": "true_forest"}


def truth(cfg: dict, lift: float) -> dict:
    """True value of a bonus by tier x channel, and of the reference rules, on notebook 08's population."""
    plan = cfg["plan"]
    pop = pd.concat([simulate(lift, seed=SEED + 1 + k)[0] for k in range(2)], ignore_index=True)
    g = guardrail.value_from_lift(pop.tau.to_numpy(), pop.p0.to_numpy(), plan)
    tiers, channels = cfg["covariates"]["tier"]["levels"], cfg["covariates"]["channel"]["levels"]
    df = pd.DataFrame({"tier": pop.tier, "channel": pop.channel, "tau": pop.tau, "p0": pop.p0, "g": g})
    cells = df.groupby(["tier", "channel"]).agg(share=("g", "size"), lift=("tau", "mean"), baseline=("p0", "mean"),
                                                value=("g", "mean")).reset_index()
    cells["share"] /= len(df)
    pays = cells.set_index(["tier", "channel"]).value > 0
    by_cell = pays.reindex(pd.MultiIndex.from_arrays([pop.tier, pop.channel])).to_numpy()
    # the cost-side rule at the true average lift: who it treats, and the baseline it cuts at
    score = cupac.score(pop, cupac.load())
    c, v = guardrail.extra_cost(plan), plan["value_per_activation_usd"]
    return {
        "cells": [{"tier": tiers[r.tier], "channel": channels[r.channel], "share": r.share, "lift": r.lift,
                   "baseline": r.baseline, "value_cents": 100 * r.value} for r in cells.itertuples()],
        "everyone_cents": 100 * float(g.mean()),
        "best_by_cell_cents": 100 * float(np.where(by_cell, g, 0).mean()),
        "best_possible_cents": 100 * float(np.where(g > 0, g, 0).mean()),
        "baseline_cutoff": (v - c) * lift / c,          # treat if the predicted baseline is below this
        "baseline_rule_share": float((score < (v - c) * lift / c).mean()),
    }


def main():
    cfg = load()
    cached = json.loads(RESULTS.read_text())
    rows = pd.DataFrame(cached["rows"])
    lift = cached["key"]["lift"]
    sizes = []
    for n, g in rows.groupby("n"):
        sizes.append({
            "players": int(n), "experiments": len(g),
            "rules": {k: {"mean": float(g[col].mean()), "q10": float(g[col].quantile(0.1)),
                          "q90": float(g[col].quantile(0.9))} for k, col in RULES.items()},
            "baseline_rule_share": float(g.share_baseline_rule.mean()),
            "forest_share": float(g.share_forest.mean()),
            "forest_beats_subgroups": float((g.true_forest > g.true_subgroups).mean()),
            "forest_beats_baseline_rule": float((g.true_forest > g.true_baseline_rule).mean()),
            "heterogeneity_found_test": float((g.p_interactions < 0.05).mean()),
            "heterogeneity_found_forest": float((g.p_blp < 0.05).mean()),
            "forest_calibration_slope": float(g.blp_slope.mean()),
        })
    out = {
        "preset_lift": lift, "planned_players": cfg["plan"]["max_players"],
        "economics": {"value_per_activation_usd": cfg["plan"]["value_per_activation_usd"],
                      "extra_cost_usd": guardrail.extra_cost(cfg["plan"])},
        "truth": truth(cfg, lift), "sizes": sizes,
    }
    OUT.write_text(json.dumps(out, indent=1))
    s = next(x for x in sizes if x["players"] == cfg["plan"]["max_players"])
    print(f"wrote {OUT.relative_to(ROOT)}: at {s['players']:,} players everyone {s['rules']['everyone']['mean']:.2f}¢, "
          f"cost-side rule {s['rules']['baseline_rule']['mean']:.2f}¢, forest {s['rules']['forest']['mean']:.2f}¢")


if __name__ == "__main__":
    main()
