import numpy as np
import pytest
from statsmodels.stats import (
    proportion as smp,  # module alias: pytest would collect test_proportions_2indep
)

from ablab.stats import diff_in_proportions, naive_interval, naive_p_value

CASES = [(11929, 50169, 11146, 50458), (230, 1012, 221, 988), (51, 240, 49, 260), (3000, 12000, 2800, 12100)]


@pytest.mark.parametrize("s_t,n_t,s_c,n_c", CASES)
def test_matches_statsmodels_wald(s_t, n_t, s_c, n_c):
    lo, hi = naive_interval(s_t, n_t, s_c, n_c)
    ref_lo, ref_hi = smp.confint_proportions_2indep(s_t, n_t, s_c, n_c, method="wald", compare="diff")
    assert lo == pytest.approx(ref_lo, rel=1e-9)
    assert hi == pytest.approx(ref_hi, rel=1e-9)
    ref_p = smp.test_proportions_2indep(s_t, n_t, s_c, n_c, method="wald", compare="diff").pvalue
    assert naive_p_value(s_t, n_t, s_c, n_c) == pytest.approx(ref_p, rel=1e-9)


def test_vectorised_equals_scalar():
    arr = np.array(CASES).T
    d, se, z = diff_in_proportions(*arr)
    for i, case in enumerate(CASES):
        d1, se1, z1 = diff_in_proportions(*case)
        assert (d[i], se[i], z[i]) == pytest.approx((d1, se1, z1))
