"""Milestone 9: CUPAC, guardrail, segments."""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from ablab import cupac, guardrail, segments
from ablab.config import load
from ablab.sequential import confidence_sequence, rho2_for
from ablab.simulator import simulate
from ablab.stats import diff_in_means, diff_in_proportions

CFG = load()
PLAN = CFG["plan"]


@pytest.fixture(scope="module")
def cohort():
    return simulate(0.0, seed=7)[0]


def test_cupac_weights_reproduce_sklearn(cohort):
    first = cohort[cohort.signup_hour < 7 * 24]
    ref = LogisticRegression(max_iter=1000).fit(cupac.design(first), first.activated)
    m = cupac.train(cohort)
    assert np.allclose(cupac.score(cohort, m), ref.predict_proba(cupac.design(cohort))[:, 1], atol=1e-9)


def test_stored_model_is_the_trained_one():
    m = cupac.load()
    again = cupac.train(simulate(0.0, seed=m["cohort_seed"])[0])
    assert again["weights"] == pytest.approx(m["weights"], rel=1e-6)
    assert again["theta"] == pytest.approx(m["theta"], rel=1e-6)


def test_cupac_reduces_variance_without_changing_the_mean(cohort):
    m = cupac.load()
    x = cupac.score(cohort, m)
    y = cohort.activated.to_numpy(float)
    y_adj = cupac.adjusted(y, x, m)
    assert abs(y_adj.mean() - y.mean()) < 0.01
    assert y_adj.var() < 0.92 * y.var()


def test_diff_in_means_of_a_binary_outcome_equals_proportions():
    rng = np.random.default_rng(1)
    y_t, y_c = rng.random(4000) < 0.25, rng.random(4100) < 0.22
    d, se, _ = diff_in_means(len(y_t), y_t.sum(), y_t.sum(), len(y_c), y_c.sum(), y_c.sum())
    d2, se2, _ = diff_in_proportions(y_t.sum(), len(y_t), y_c.sum(), len(y_c))
    assert d == pytest.approx(d2)
    assert se == pytest.approx(se2, rel=1e-3)  # sample (n-1) vs plug-in (n) variance


@pytest.mark.parametrize("lo,hi,expected", [(-0.03, -0.001, "red"), (0.001, 0.03, "green"), (-0.01, 0.02, "grey")])
def test_guardrail_light(lo, hi, expected):
    assert guardrail.light(lo, hi) == expected


@pytest.mark.parametrize("lift,pays,expected", [("ship", "red", "doesnt_pay"), ("ship", "grey", "ship"),
                                                ("ship", "green", "ship"), ("keep_collecting", "red", "keep_collecting"),
                                                ("dont_ship", "red", "dont_ship")])
def test_final_verdict(lift, pays, expected):
    assert guardrail.final_verdict(lift, pays) == expected


def test_guardrail_value_matches_break_even():
    """Value per player is zero exactly at the break-even lift (notebook 04)."""
    from ablab.power import break_even_lift
    be = break_even_lift(0.22, PLAN["p_reach_level10"], PLAN["bonus_usd"], PLAN["value_per_activation_usd"])
    v_c = 0.22 * PLAN["value_per_activation_usd"]
    v_t = (0.22 + be) * (PLAN["value_per_activation_usd"] - guardrail.extra_cost(PLAN))
    assert v_t == pytest.approx(v_c)


def test_segment_levels_and_shares():
    lv = segments.levels(CFG)
    assert len(lv) == 8
    for dim in ("Country tier", "Device", "Channel"):
        assert sum(s for d, _, s in lv if d == dim) == pytest.approx(1.0)


def test_one_segment_covering_everyone_is_the_overall_interval():
    s_t, n_t, s_c, n_c = 2400, 10000, 2200, 10100
    d, se, _ = diff_in_proportions(s_t, n_t, s_c, n_c)
    lo, hi = confidence_sequence(d, se, n_t + n_c, rho2_for(PLAN["n_star"]))
    assert segments.segment_interval(s_t, n_t, s_c, n_c, 1.0, 1, PLAN["alpha"], PLAN["n_star"]) == pytest.approx((lo, hi))


def test_value_from_lift_is_zero_at_break_even_and_increasing():
    from ablab.power import break_even_lift
    p_c = 0.22
    be = break_even_lift(p_c, PLAN["p_reach_level10"], PLAN["bonus_usd"], PLAN["value_per_activation_usd"])
    assert guardrail.value_from_lift(be, p_c, PLAN) == pytest.approx(0, abs=1e-12)
    lifts = np.linspace(-0.05, 0.08, 50)
    assert (np.diff(guardrail.value_from_lift(lifts, p_c, PLAN)) > 0).all()
