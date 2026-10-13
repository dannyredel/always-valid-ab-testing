"""Validity evidence 1-3 (brief section 7) at the planned settings in config/simulator.toml.

Simulates experiments looked at after every page refresh and after every 50 players, under each
preset, and writes results/always_valid.json. Exits with status 1 if a threshold is missed.

    python -m validity.always_valid
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
from statsmodels.stats.proportion import proportion_confint

from ablab.config import load
from ablab.sequential import confidence_sequence, rho2_for, running_intersection
from ablab.simulator import simulate_counts
from ablab.stats import Z95, diff_in_proportions

RUNS = 2_000
SEED = 20261016
OUT = Path(__file__).resolve().parent.parent / "results" / "always_valid.json"


def rate(hits: np.ndarray) -> dict:
    k, n = int(hits.sum()), len(hits)
    lo, hi = proportion_confint(k, n, method="wilson")
    return {"rate": k / n, "ci_low": lo, "ci_high": hi, "runs": n}


def study(lift: float, batch: float, rng: np.random.Generator, cfg: dict) -> dict:
    plan = cfg["plan"]
    looks = int(np.ceil(plan["max_players"] / batch))
    c = simulate_counts(lift, rng, RUNS, looks, batch, base=cfg["experiment"]["baseline_rate"])
    d, se, _ = diff_in_proportions(c["s_t"], c["n_t"], c["s_c"], c["n_c"])
    n = c["n_t"] + c["n_c"]
    live = (n >= plan["min_players"]) & (n <= plan["max_players"])
    lo, hi = confidence_sequence(d, se, n, rho2_for(plan["n_star"], plan["alpha"]), plan["alpha"])
    lo, hi = running_intersection(lo, hi, n, plan["min_players"])          # what the page shows
    nlo, nhi = d - Z95 * se, d + Z95 * se
    return {
        "looks_per_run": looks,
        "always_valid": {
            "false_verdict": rate((((lo > 0) | (hi < 0)) & live).any(1)) if lift == 0 else None,
            "coverage_every_look": rate((((lo <= lift) & (lift <= hi)) | ~live).all(1)),
            "ship_by_max": rate(((lo > 0) & live).any(1)),
        },
        "usual_interval": {
            "false_verdict": rate((((nlo > 0) | (nhi < 0)) & live).any(1)) if lift == 0 else None,
            "coverage_every_look": rate((((nlo <= lift) & (lift <= nhi)) | ~live).all(1)),
        },
    }


def main() -> int:
    cfg = load()
    plan, page = cfg["plan"], cfg["page"]
    players_per_update = cfg["arrivals"]["per_hour"] * page["hours_per_update"]
    rng = np.random.default_rng(SEED)
    results = {"date": date.today().isoformat(), "seed": SEED, "runs": RUNS,
               "alpha": plan["alpha"], "n_star": plan["n_star"], "min_players": plan["min_players"],
               "max_players": plan["max_players"], "checks": {}}
    ok = True
    for name, lift in zip(cfg["presets"]["names"], cfg["presets"]["lifts"]):
        for cadence, batch in [("every live update", players_per_update), ("every 50 players", 50)]:
            r = study(lift, batch, rng, cfg)
            results["checks"][f"{name} | {cadence}"] = r
            av = r["always_valid"]
            if lift == 0:
                passed = av["false_verdict"]["ci_low"] <= plan["alpha"]          # evidence 1
                ok &= passed
                print(f"[{'PASS' if passed else 'FAIL'}] evidence 1  {name:<18} {cadence:<19} "
                      f"false verdicts {av['false_verdict']['rate']:.2%}  "
                      f"(usual interval: {r['usual_interval']['false_verdict']['rate']:.1%}, evidence 3)")
            passed = av["coverage_every_look"]["ci_high"] >= 1 - plan["alpha"]    # evidence 2
            ok &= passed
            print(f"[{'PASS' if passed else 'FAIL'}] evidence 2  {name:<18} {cadence:<19} "
                  f"coverage {av['coverage_every_look']['rate']:.2%}  "
                  f"(usual: {r['usual_interval']['coverage_every_look']['rate']:.1%});  "
                  f"ship by max {av['ship_by_max']['rate']:.1%}")
    results["all_passed"] = bool(ok)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2))
    print(f"wrote {OUT.relative_to(OUT.parent.parent)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
