"""Write the shared fixtures the TypeScript port must reproduce (validity evidence 4).

    python -m scripts.make_fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ablab import cupac, guardrail, segments
from ablab.assign import assignment_u
from ablab.checks import smd_from_counts, srm_log_bayes_factor
from ablab.config import load
from ablab.sequential import (
    always_valid_p,
    confidence_sequence,
    cs_multiplier,
    p_value_at_look,
    rho2_for,
    running_intersection,
    verdict,
)
from ablab.simulator import simulate, simulate_counts
from ablab.stats import diff_in_means, diff_in_proportions, naive_interval, naive_p_value

OUT = Path(__file__).resolve().parent.parent / "fixtures"


def assign_fixture(cfg):
    key = cfg["experiment"]["key"]
    ids = [f"Q{i:07d}" for i in range(200)] + ["", "a", "player-ü", "x" * 37]
    return {"key": key, "cases": [{"player_id": p, "u": assignment_u(p, key)} for p in ids]}


def stats_fixture(rng):
    cases = []
    for _ in range(60):
        n_t, n_c = (int(x) for x in rng.integers(200, 60_000, 2))
        p = rng.uniform(0.05, 0.6)
        s_t, s_c = int(rng.binomial(n_t, p + rng.uniform(-0.03, 0.03))), int(rng.binomial(n_c, p))
        d, se, z = diff_in_proportions(s_t, n_t, s_c, n_c)
        lo, hi = naive_interval(s_t, n_t, s_c, n_c)
        cases.append({"s_t": s_t, "n_t": n_t, "s_c": s_c, "n_c": n_c, "d": float(d), "se": float(se),
                      "z": float(z), "lo": float(lo), "hi": float(hi),
                      "p": float(naive_p_value(s_t, n_t, s_c, n_c))})
    return {"cases": cases}


def sequential_fixture(rng, cfg):
    plan = cfg["plan"]
    rho2 = rho2_for(plan["n_star"], plan["alpha"])
    out = {"alpha": plan["alpha"], "n_star": plan["n_star"], "rho2": rho2, "min_players": plan["min_players"],
           "max_players": plan["max_players"],
           "multiplier": [{"n": n, "c": float(cs_multiplier(n, rho2, plan["alpha"]))}
                          for n in (100, 1_000, 5_000, 30_000, 100_000)],
           "paths": []}
    for lift in (0.0, 0.02, 0.05, -0.03):
        c = simulate_counts(lift, rng, runs=1, looks=70, batch=450)
        s_t, n_t, s_c, n_c = (c[k][0] for k in ("s_t", "n_t", "s_c", "n_c"))
        d, se, z = diff_in_proportions(s_t, n_t, s_c, n_c)
        n = n_t + n_c
        lo, hi = confidence_sequence(d, se, n, rho2, plan["alpha"])
        ilo, ihi = running_intersection(lo, hi, n, plan["min_players"])
        out["paths"].append({
            "lift": lift,
            "looks": [{"s_t": int(a), "n_t": int(b), "s_c": int(e), "n_c": int(f), "lo": float(g), "hi": float(h),
                       "lo_intersected": None if np.isinf(i) else float(i),
                       "hi_intersected": None if np.isinf(j) else float(j),
                       "p_at_look": float(k), "p_always_valid": float(m),
                       "verdict": verdict(i, j, nn, plan["min_players"], plan["max_players"])}
                      for a, b, e, f, g, h, i, j, k, m, nn in zip(
                          s_t, n_t, s_c, n_c, lo, hi, ilo, ihi, p_value_at_look(z, n, rho2),
                          always_valid_p(z, n, rho2), n)],
        })
    return out


def checks_fixture(rng):
    srm = [{"n_c": int(c), "n_t": int(t), "log_bf": srm_log_bayes_factor(int(c), int(t))}
           for c, t in [(5000, 5000), (5200, 4800), (101, 99), (0, 0), (3, 0)]
           + [tuple(rng.integers(10, 40_000, 2)) for _ in range(30)]]
    smd = []
    for _ in range(30):
        n_c, n_t = (int(x) for x in rng.integers(50, 20_000, 2))
        k_c, k_t = int(rng.binomial(n_c, 0.3)), int(rng.binomial(n_t, 0.31))
        smd.append({"k_c": k_c, "n_c": n_c, "k_t": k_t, "n_t": n_t, "smd": smd_from_counts(k_c, n_c, k_t, n_t)})
    return {"srm": srm, "smd": smd}


def m9_fixture(rng, cfg):
    plan = cfg["plan"]
    model = cupac.load()
    players = simulate(0.02, seed=4321)[0].sample(60, random_state=1)
    x = cupac.score(players, model)
    score_cases = [{"evening": bool(r.evening), "games_30d": int(r.games_30d), "click_to_install_s": float(r.click_to_install_s),
                    "partner_score": None if np.isnan(r.partner_score) else float(r.partner_score),
                    "tier": int(r.tier), "device": int(r.device), "channel": int(r.channel), "activated": bool(r.activated),
                    "x": float(xi), "y_adj": float(cupac.adjusted(float(r.activated), xi, model))}
                   for r, xi in zip(players.itertuples(), x)]
    means = []
    rho2 = rho2_for(plan["n_star"], plan["alpha"])
    for _ in range(30):
        n_t, n_c = (int(v) for v in rng.integers(1_000, 30_000, 2))
        y_t, y_c = rng.normal(0.24, 0.4, n_t), rng.normal(0.22, 0.4, n_c)
        sums = {"n_t": n_t, "s_t": float(y_t.sum()), "ss_t": float((y_t**2).sum()),
                "n_c": n_c, "s_c": float(y_c.sum()), "ss_c": float((y_c**2).sum())}
        d, se, _ = diff_in_means(**sums)
        lo, hi = confidence_sequence(d, se, n_t + n_c, rho2, plan["alpha"])
        means.append({**sums, "d": float(d), "se": float(se), "lo": float(lo), "hi": float(hi), "light": guardrail.light(lo, hi)})
    lv = segments.levels(cfg)
    seg_cases = []
    for (dim, level, share) in lv:
        for _ in range(3):
            n_t, n_c = (int(v) for v in rng.integers(300, 12_000, 2))
            s_t, s_c = int(rng.binomial(n_t, 0.23)), int(rng.binomial(n_c, 0.22))
            lo, hi = segments.segment_interval(s_t, n_t, s_c, n_c, share, len(lv), plan["alpha"], plan["n_star"])
            seg_cases.append({"level": level, "share": share, "s_t": s_t, "n_t": n_t, "s_c": s_c, "n_c": n_c, "lo": float(lo), "hi": float(hi)})
    return {"cupac": {k: model[k] for k in ("columns", "intercept", "weights", "theta", "mu")}, "score_cases": score_cases,
            "means": means, "segments": {"k": len(lv), "levels": [[d, lvl, sh] for d, lvl, sh in lv], "cases": seg_cases},
            "extra_cost": guardrail.extra_cost(plan)}


def main():
    cfg = load()
    rng = np.random.default_rng(20261017)
    OUT.mkdir(exist_ok=True)
    for name, data in [("assign", assign_fixture(cfg)), ("stats", stats_fixture(rng)),
                       ("sequential", sequential_fixture(rng, cfg)), ("checks", checks_fixture(rng)), ("m9", m9_fixture(rng, cfg))]:
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=1))
        print(f"wrote fixtures/{name}.json")


if __name__ == "__main__":
    main()
