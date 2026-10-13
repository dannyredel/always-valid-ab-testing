import numpy as np
import pandas as pd
import pytest
from scipy.stats import chisquare
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from ablab.checks import smd_from_counts, srm_always_valid_p, srm_chi2, srm_log_bayes_factor
from ablab.config import load
from ablab.power import break_even_lift, fixed_horizon_n, sequential_power

PLAN = load()["plan"]


def test_break_even_from_config():
    be = break_even_lift(0.22, PLAN["p_reach_level10"], PLAN["bonus_usd"], PLAN["value_per_activation_usd"])
    assert be == pytest.approx(0.01707, abs=1e-4)
    # at break-even, extra value equals extra cost
    assert be * PLAN["value_per_activation_usd"] == pytest.approx((0.22 + be) * 0.45 * PLAN["bonus_usd"])


@pytest.mark.parametrize("lift", [0.01, 0.0171, 0.02, 0.05])
def test_fixed_n_matches_statsmodels(lift):
    per_arm = NormalIndPower().solve_power(effect_size=proportion_effectsize(0.22 + lift, 0.22), alpha=0.05,
                                           power=0.8, ratio=1)
    assert fixed_horizon_n(0.22, lift) == pytest.approx(2 * per_arm, rel=0.01)


def test_planned_maximum_gives_80_percent_power():
    """Notebook 04: N_max = 30,000 with CUPAC gives at least 80% power at break-even."""
    be = break_even_lift(0.22, PLAN["p_reach_level10"], PLAN["bonus_usd"], PLAN["value_per_activation_usd"])
    power, _ = sequential_power(0.22, be, PLAN["max_players"], np.random.default_rng(3), runs=2_000,
                                variance_factor=1 - PLAN["cupac_r2"])
    assert power >= 0.78  # 0.80 within simulation error (SE about 0.009)


@pytest.mark.parametrize("n_c,n_t", [(5000, 5000), (5200, 4800), (50458, 50169), (101, 99)])
def test_srm_matches_scipy(n_c, n_t):
    assert srm_chi2(n_c, n_t) == pytest.approx(chisquare([n_c, n_t]).pvalue, rel=1e-9)


def test_smd_matches_causalml():
    from causalml.match import create_table_one

    rng = np.random.default_rng(0)
    df = pd.DataFrame({"treated": rng.integers(0, 2, 3000), "x": rng.random(3000) < 0.3})
    df["x"] = df.x.astype(int)
    ref = float(create_table_one(df, "treated", ["x"]).loc["x", "SMD"])
    c, t = df[df.treated == 0].x, df[df.treated == 1].x
    assert smd_from_counts(c.sum(), len(c), t.sum(), len(t)) == pytest.approx(ref, abs=1e-4)  # causalml rounds to 4


# Reference values from savvi 0.3.1 (Multinomial, theta_0 = [0.5, 0.5], k = 100), computed in a separate
# environment because savvi pulls in cvxpy: log(odds) after updating with these counts.
SAVVI = [((5000, 5000), -2.310035464264729), ((5200, 4800), 5.613613411771439),
         ((50458, 50169), -3.045401357478113), ((101, 99), -0.5442837827312416),
         ((1500, 1350), 2.1218886818951432), ((12000, 11500), 2.5628257064199715)]


@pytest.mark.parametrize("counts,log_odds", SAVVI)
def test_srm_bayes_factor_matches_savvi(counts, log_odds):
    assert srm_log_bayes_factor(*counts) == pytest.approx(log_odds, rel=1e-9)


def test_srm_batches_telescope():
    """savvi updated in three batches ([300,280],[250,310],[400,390]) equals one update with the totals."""
    assert srm_log_bayes_factor(950, 980) == pytest.approx(-1.2858950549379526, rel=1e-9)


def test_srm_always_valid_p_only_falls_and_flags_broken_split():
    rng = np.random.default_rng(5)
    n = rng.poisson(450, 70)
    fair_t = rng.binomial(n, 0.5).cumsum()
    p_fair = srm_always_valid_p(n.cumsum() - fair_t, fair_t)
    assert (np.diff(p_fair) <= 0).all()
    broken_t = rng.binomial(n, 0.53).cumsum()
    assert srm_always_valid_p(n.cumsum() - broken_t, broken_t)[-1] < 0.001
