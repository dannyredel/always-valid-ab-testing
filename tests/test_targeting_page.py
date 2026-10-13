"""The page's targeting numbers come from notebook 08's cached experiments (scripts/targeting_page.py)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.targeting_page import OUT, RESULTS, RULES

pytestmark = pytest.mark.skipif(not (OUT.exists() and RESULTS.exists()), reason="run notebook 08 and the script first")


def test_rule_values_match_cached_experiments():
    page = json.loads(Path(OUT).read_text())
    rows = pd.DataFrame(json.loads(Path(RESULTS).read_text())["rows"])
    for size in page["sizes"]:
        g = rows[rows.n == size["players"]]
        assert size["experiments"] == len(g) > 0
        for rule, col in RULES.items():
            assert size["rules"][rule]["mean"] == pytest.approx(g[col].mean(), rel=1e-12)
        assert size["heterogeneity_found_test"] == pytest.approx((g.p_interactions < 0.05).mean())


def test_truth_is_consistent():
    t = json.loads(Path(OUT).read_text())["truth"]
    cells = pd.DataFrame(t["cells"])
    assert cells.share.sum() == pytest.approx(1.0)
    assert (cells.share * cells.value_cents).sum() == pytest.approx(t["everyone_cents"], rel=1e-9)
    assert t["everyone_cents"] < t["best_by_cell_cents"] < t["best_possible_cents"]
