import numpy as np
import pytest

from ablab.config import load
from ablab.simulator import calibrate, day_shape, hour_shape, simulate

CFG = load()


@pytest.fixture(scope="module")
def small_run():
    return simulate(0.02, seed=20261012)[0]


def test_shapes_average_one():
    assert hour_shape().mean() == pytest.approx(1.0)
    assert day_shape().mean() == pytest.approx(1.0)


def test_stored_calibration_matches_world():
    b0, mult = calibrate(n_ref=200_000, seed=1)
    assert b0 == pytest.approx(CFG["calibration"]["intercept"], abs=0.01)
    assert mult == pytest.approx(CFG["calibration"]["multiplier_mean"], abs=0.005)


def test_baseline_and_true_lift(small_run):
    assert small_run.p0.mean() == pytest.approx(CFG["experiment"]["baseline_rate"], abs=0.005)
    assert (small_run.p1 - small_run.p0).mean() == pytest.approx(0.02, abs=0.001)


def test_no_effect_preset_has_zero_lift():
    df, _ = simulate(0.0, seed=7)
    assert (df.p1 - df.p0).abs().max() == 0


def test_split_and_determinism(small_run):
    assert abs(small_run.treated.mean() - 0.5) < 0.01
    again, _ = simulate(0.02, seed=20261012)
    assert again.activated.equals(small_run.activated)


def test_signals_track_engagement(small_run):
    assert np.corrcoef(np.log1p(small_run.games_30d), small_run.engagement)[0, 1] > 0.3
    assert np.corrcoef(np.log(small_run.click_to_install_s), small_run.engagement)[0, 1] < -0.2
    paid = small_run.channel == CFG["covariates"]["channel"]["levels"].index("Paid social")
    assert small_run.partner_score[paid].notna().all()
    assert small_run.partner_score[~paid].isna().all()


def test_activations_land_inside_window(small_run):
    done = small_run[small_run.activated]
    assert (done.hours_to_milestone < CFG["plan"]["outcome_delay_h"]).all()


def test_late_start_does_not_hang():
    # seed 20263027 draws an activated player whose first start falls after the window (about 1 in 50
    # million): the journey loop used to redraw only the milestone and never ended (found in notebook 08)
    df, _ = simulate(0.02, seed=20263027)
    done = df[df.activated]
    assert (done.hours_to_start < CFG["plan"]["outcome_delay_h"]).all()
    assert (done.hours_to_milestone < CFG["plan"]["outcome_delay_h"]).all()
