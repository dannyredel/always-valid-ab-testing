"""Segment monitoring (notebook 05): familywise coverage of the 8 widened intervals, and harm detection.

Exact per-cell simulation (3 tiers x 2 devices x 3 channels), looks at every live update.
Writes results/segments.json; exits 1 if familywise coverage misses 95%.

    python -m validity.segments
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
from scipy.special import expit
from statsmodels.stats.proportion import proportion_confint

from ablab import segments
from ablab.config import load
from ablab.sequential import cs_multiplier, rho2_for
from ablab.simulator import day_shape, draw_covariates, hour_shape, linear_predictor, raw_multiplier

SEED, RUNS = 20261021, 2_000
OUT = Path(__file__).resolve().parent.parent / "results" / "segments.json"


def rate(hits) -> dict:
    k, n = int(np.sum(hits)), len(hits)
    lo, hi = proportion_confint(k, n, method="wilson")
    return {"rate": k / n, "ci_low": lo, "ci_high": hi}


def main() -> int:
    cfg = load()
    plan = cfg["plan"]
    rng = np.random.default_rng(SEED)
    ref = draw_covariates(rng.choice(24 * 7, 400_000, p=np.outer(day_shape(), hour_shape()).ravel() / 168), rng)
    ref["p0"] = expit(cfg["calibration"]["intercept"] + linear_predictor(ref))
    ref["m"] = np.asarray(raw_multiplier(ref)) / cfg["calibration"]["multiplier_mean"]
    cells = ref.groupby(["tier", "device", "channel"]).agg(share=("p0", "size"), p0=("p0", "mean"), m=("m", "mean")).reset_index()
    cells["share"] /= cells.share.sum()
    lv = segments.levels(cfg)
    names = cfg["covariates"]
    col = {"Country tier": ("tier", names["tier"]["levels"]), "Device": ("device", names["device"]["levels"]),
           "Channel": ("channel", names["channel"]["levels"])}
    member = np.stack([(cells[col[d][0]] == col[d][1].index(level)).to_numpy() for d, level, _ in lv], 1).astype(float)
    shares = np.array([s for _, _, s in lv])
    k = len(lv)
    batch = cfg["arrivals"]["per_hour"] * cfg["page"]["hours_per_update"]
    looks = int(np.ceil(plan["max_players"] / batch))

    def run(lift, mult):
        p0, p1 = cells.p0.to_numpy(), np.clip(cells.p0.to_numpy() + lift * mult, 0, 1)
        probs = np.concatenate([cells.share.to_numpy() / 2] * 2)
        n = rng.multinomial(rng.poisson(batch, (RUNS, looks)), probs)
        s = rng.binomial(n, np.concatenate([p0, p1]))
        cnum = len(cells)
        tot = {key: arr.cumsum(1) @ member for key, arr in
               (("n_c", n[..., :cnum]), ("n_t", n[..., cnum:]), ("s_c", s[..., :cnum]), ("s_t", s[..., cnum:]))}
        with np.errstate(divide="ignore", invalid="ignore"):
            p_t, p_c = tot["s_t"] / tot["n_t"], tot["s_c"] / tot["n_c"]
            d = p_t - p_c
            se = np.sqrt(p_t * (1 - p_t) / tot["n_t"] + p_c * (1 - p_c) / tot["n_c"])
            nn = tot["n_t"] + tot["n_c"]
            a = plan["alpha"] / k
            half = se * cs_multiplier(nn, rho2_for(plan["n_star"] * shares, a), a)
        early = (nn < segments.MIN_PLAYERS) | ~np.isfinite(half)
        lo = np.maximum.accumulate(np.where(early, -np.inf, d - half), 1)
        hi = np.minimum.accumulate(np.where(early, np.inf, d + half), 1)
        w = cells.share.to_numpy()[:, None] * member
        truth = lift * (mult[:, None] * w).sum(0) / w.sum(0)
        return lo, hi, truth

    lo, hi, truth = run(0.02, cells.m.to_numpy())
    familywise = rate(((lo <= truth) & (truth <= hi)).all(axis=(1, 2)))
    harm_m = cells.m.to_numpy().copy()
    harm_m[cells.tier.to_numpy() == 0] = -1.2
    _, hhi, htruth = run(0.02, harm_m)
    harmed = htruth < 0
    detect = rate((hhi[..., harmed] < 0).any(axis=(1, 2)))
    false_flag = rate((hhi[..., ~harmed] < 0).any(axis=(1, 2)))
    ok = familywise["ci_high"] >= 1 - plan["alpha"]
    res = {"date": date.today().isoformat(), "seed": SEED, "runs": RUNS, "segments": [f"{d}: {lvl}" for d, lvl, _ in lv],
           "familywise_coverage_small": familywise, "harm_scenario": {"tier1_true_lift": float(htruth[0]),
           "detected_by_max": detect, "unharmed_falsely_flagged": false_flag}, "all_passed": bool(ok)}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(f"[{'PASS' if ok else 'FAIL'}] familywise coverage (8 segments, every look): {familywise['rate']:.1%}")
    print(f"       harm scenario: tier 1 ({htruth[0] * 100:+.1f} pts) detected {detect['rate']:.1%}, "
          f"unharmed falsely flagged {false_flag['rate']:.2%}")
    print(f"wrote {OUT.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
