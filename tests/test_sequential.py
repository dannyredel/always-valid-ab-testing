import numpy as np
import pytest

from ablab.sequential import (
    always_valid_p,
    confidence_sequence,
    cs_multiplier,
    p_value_at_look,
    rho2_for,
    running_intersection,
    verdict,
)
from ablab.simulator import simulate_counts
from ablab.stats import diff_in_proportions

gb = pytest.importorskip("gbstats.frequentist.tests", reason="install with: uv pip install --no-deps gbstats pydantic")
from gbstats.models.statistics import ProportionStatistic

ALPHA, N_STAR = 0.05, 30_000


@pytest.fixture(scope="module")
def paths():
    c = simulate_counts(0.0, np.random.default_rng(1), runs=200, looks=200, batch=100)
    d, se, z = diff_in_proportions(c["s_t"], c["n_t"], c["s_c"], c["n_c"])
    return c, d, se, z, c["n_t"] + c["n_c"]


@pytest.mark.parametrize("s_t,n_t,s_c,n_c", [(11929, 50169, 11146, 50458), (530, 2410, 498, 2390),
                                             (2400, 10000, 2200, 10100), (120, 600, 131, 590)])
def test_matches_gbstats(s_t, n_t, s_c, n_c):
    d, se, z = diff_in_proportions(s_t, n_t, s_c, n_c)
    n = n_t + n_c
    rho2 = rho2_for(N_STAR, ALPHA)
    lo, hi = confidence_sequence(d, se, n, rho2, ALPHA)
    cfg = gb.SequentialConfig(difference_type="absolute", alpha=ALPHA, sequential_tuning_parameter=N_STAR)
    ref = gb.SequentialTwoSidedTTest(ProportionStatistic(sum=s_c, n=n_c), ProportionStatistic(sum=s_t, n=n_t),
                                     cfg).compute_result()
    assert (lo, hi) == pytest.approx(tuple(ref.ci), rel=1e-9)
    assert p_value_at_look(z, n, rho2) == pytest.approx(ref.p_value, rel=1e-9)


def test_wider_than_usual_interval():
    assert (cs_multiplier(np.array([1e3, 1e4, 3e4, 1e5]), rho2_for(N_STAR)) > 1.96).all()


def test_tightest_near_n_star():
    """The multiplier's minimum lies close to the tuning size."""
    n = np.logspace(3, 6, 2000)
    n_min = n[np.argmin(cs_multiplier(n, rho2_for(N_STAR)))]
    assert N_STAR / 3 < n_min < N_STAR * 3


def test_p_value_never_increases(paths):
    _, _, _, z, n = paths
    p = always_valid_p(z, n, rho2_for(N_STAR))
    assert (np.diff(p, axis=1) <= 1e-15).all()


def test_p_below_alpha_exactly_when_some_interval_excluded_zero(paths):
    _, d, se, z, n = paths
    rho2 = rho2_for(5_000)  # small N* so that some null paths cross
    lo, hi = confidence_sequence(d, se, n, rho2)
    ever_excluded = np.logical_or.accumulate((lo > 0) | (hi < 0), axis=1)
    assert ever_excluded[:, -1].any()  # some paths do cross, so the check is not vacuous
    assert np.array_equal(always_valid_p(z, n, rho2) < ALPHA, ever_excluded)


def test_running_intersection_only_narrows_and_skips_early_looks(paths):
    _, d, se, _, n = paths
    lo, hi = confidence_sequence(d, se, n, rho2_for(N_STAR))
    ilo, ihi = running_intersection(lo, hi, n, min_n=1_000)
    with np.errstate(invalid="ignore"):  # -inf minus -inf on the masked early looks
        assert not (np.diff(ilo, axis=1) < 0).any() and not (np.diff(ihi, axis=1) > 0).any()
    early = n < 1_000
    assert np.isneginf(ilo[early]).all() and np.isposinf(ihi[early]).all()


@pytest.mark.parametrize("lo,hi,n,expected", [
    (0.001, 0.03, 5_000, "ship"), (-0.03, -0.001, 5_000, "dont_ship"), (-0.01, 0.02, 5_000, "keep_collecting"),
    (0.001, 0.03, 500, "keep_collecting"), (-0.01, 0.02, 30_000, "inconclusive"),
])
def test_verdict_rules(lo, hi, n, expected):
    assert verdict(lo, hi, n, min_n=1_000, max_n=30_000) == expected
