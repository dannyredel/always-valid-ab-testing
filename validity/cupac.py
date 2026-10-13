"""Validity of the CUPAC-adjusted interval and behaviour of the guardrail (notebook 06).

Draws 30,000-player experiments from a large pool built with the production simulator and the stored
CUPAC model (config/cupac.json), looks every 500 players, and writes results/cupac.json.
Exits 1 if the adjusted interval misses evidence 1 or 2.

    python -m validity.cupac
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
from statsmodels.stats.proportion import proportion_confint

from ablab import cupac, guardrail
from ablab.config import load
from ablab.power import break_even_lift
from ablab.sequential import cs_multiplier, rho2_for
from ablab.simulator import raw_multiplier, simulate

SEED, RUNS, CHUNK, LOOK = 20261020, 1_000, 100, 500
OUT = Path(__file__).resolve().parent.parent / "results" / "cupac.json"


def rate(hits) -> dict:
    k, n = int(np.sum(hits)), len(hits)
    lo, hi = proportion_confint(k, n, method="wilson")
    return {"rate": k / n, "ci_low": lo, "ci_high": hi}


def main() -> int:
    cfg, model = load(), cupac.load()
    plan = cfg["plan"]
    n_max, min_n, alpha = plan["max_players"], plan["min_players"], plan["alpha"]
    looks = n_max // LOOK
    v, c = plan["value_per_activation_usd"], guardrail.extra_cost(plan)
    pool = [simulate(0.0, seed=SEED + k)[0] for k in range(4)]
    p0 = np.concatenate([p.p0.to_numpy() for p in pool])
    m = np.concatenate([np.asarray(raw_multiplier(p)) for p in pool]) / cfg["calibration"]["multiplier_mean"]
    x = np.concatenate([cupac.score(p, model) for p in pool])
    rng = np.random.default_rng(SEED)

    def interval(tot, name):
        n_t, n_c = tot["n_t"], tot["n_c"]
        m_t, m_c = tot[f"{name}_t"] / n_t, tot[f"{name}_c"] / n_c
        v_t = (tot[f"{name}_t2"] - n_t * m_t**2) / (n_t - 1)
        v_c = (tot[f"{name}_c2"] - n_c * m_c**2) / (n_c - 1)
        d, se, n = m_t - m_c, np.sqrt(v_t / n_t + v_c / n_c), n_t + n_c
        half = se * cs_multiplier(n, rho2_for(plan["n_star"], alpha), alpha)
        lo = np.maximum.accumulate(np.where(n >= min_n, d - half, -np.inf), 1)
        hi = np.minimum.accumulate(np.where(n >= min_n, d + half, np.inf), 1)
        return lo, hi, n

    def scenario(lift):
        parts = []
        for _ in range(RUNS // CHUNK):
            idx = rng.integers(0, len(p0), (CHUNK, n_max))
            arm = rng.random((CHUNK, n_max)) < 0.5
            y = (rng.random((CHUNK, n_max)) < p0[idx] + arm * lift * m[idx]).astype(float)
            vals = {"raw": y, "adj": cupac.adjusted(y, x[idx], model), "g": np.where(arm, (v - c) * y, v * y)}
            tot = {}
            for a, mask in (("t", arm), ("c", ~arm)):
                tot[f"n_{a}"] = mask.reshape(CHUNK, looks, LOOK).sum(2).cumsum(1)
                for k, val in vals.items():
                    vv = np.where(mask, val, 0.0).reshape(CHUNK, looks, LOOK)
                    tot[f"{k}_{a}"] = vv.sum(2).cumsum(1)
                    tot[f"{k}_{a}2"] = (vv**2).sum(2).cumsum(1)
            parts.append(tot)
        tot = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        return {k: interval(tot, k) for k in ("raw", "adj", "g")}

    be = break_even_lift(cfg["experiment"]["baseline_rate"], plan["p_reach_level10"], plan["bonus_usd"], v)
    scenarios = {"No effect": 0.0, "Below break-even (+1.0)": 0.01, "Small (+2.0)": 0.02, "Large (+5.0)": 0.05}
    res = {"date": date.today().isoformat(), "seed": SEED, "runs": RUNS, "break_even": be,
           "cupac_r2_holdout": model["r2_holdout"], "scenarios": {}}
    ok = True
    for name, lift in scenarios.items():
        out = scenario(lift)
        (alo, ahi, _), (rlo, rhi, _), _ = out["adj"], out["raw"], out["g"]
        p_c = cfg["experiment"]["baseline_rate"]  # plug-in; the page uses the running control rate
        glo, ghi = guardrail.value_from_lift(alo, p_c, plan), guardrail.value_from_lift(ahi, p_c, plan)
        ship_works = ((alo > 0) & ~(ghi < 0)).any(1)
        row = {
            "adjusted_false_verdicts": rate(((alo > 0) | (ahi < 0)).any(1)) if lift == 0 else None,
            "adjusted_coverage": rate(((alo <= lift) & (lift <= ahi)).all(1)),
            "unadjusted_coverage": rate(((rlo <= lift) & (lift <= rhi)).all(1)),
            "ships_it_works_rule": rate(ship_works),
            "guardrail_green_by_max": rate((glo > 0).any(1)),
            "guardrail_red_by_max": rate((ghi < 0).any(1)),
        }
        res["scenarios"][name] = row
        if lift == 0:
            passed = row["adjusted_false_verdicts"]["ci_low"] <= alpha
            ok &= passed
            print(f"[{'PASS' if passed else 'FAIL'}] CUPAC false verdicts, no effect: {row['adjusted_false_verdicts']['rate']:.2%}")
        passed = row["adjusted_coverage"]["ci_high"] >= 1 - alpha
        ok &= passed
        print(f"[{'PASS' if passed else 'FAIL'}] CUPAC coverage, {name}: {row['adjusted_coverage']['rate']:.1%}; "
              f"ships (brief rule) {row['ships_it_works_rule']['rate']:.1%}; guardrail red by max {row['guardrail_red_by_max']['rate']:.1%}")
    res["all_passed"] = bool(ok)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(f"wrote {OUT.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
