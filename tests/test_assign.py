import mmh3
import numpy as np
from scipy.stats import kstest

from ablab.assign import assignment_u, assignment_us, is_treated

KEY = "starter-bonus-v1"


def test_matches_reference_murmur3_vector():
    # Published MurmurHash3 x86_32 test vector: "hello", seed 0 -> 0x248bfa47
    assert mmh3.hash("hello", 0, signed=False) == 0x248BFA47
    assert assignment_u("hello", "x") == mmh3.hash("hello:x", 0, signed=False) / 2**32


def test_deterministic_and_in_unit_interval():
    ids = [f"Q{i:07d}" for i in range(1000)]
    u1, u2 = assignment_us(ids, KEY), assignment_us(ids, KEY)
    assert np.array_equal(u1, u2)
    assert (u1 >= 0).all() and (u1 < 1).all()


def test_uniform_and_fair_split():
    u = assignment_us([f"Q{i:07d}" for i in range(20_000)], KEY)
    assert kstest(u, "uniform").pvalue > 0.01
    assert abs(is_treated(u).mean() - 0.5) < 0.015


def test_experiment_key_reshuffles_players():
    ids = [f"Q{i:07d}" for i in range(5_000)]
    a = is_treated(assignment_us(ids, KEY))
    b = is_treated(assignment_us(ids, "another-test"))
    assert 0.45 < (a == b).mean() < 0.55  # independent splits agree about half the time
