# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python (ablab)
#     language: python
#     name: ablab
# ---

# %% [markdown]
# # 08 · Ship it to whom? Targeting the Starter Bonus with a causal forest
#
# **Question.** The test says the Starter Bonus works. It costs money, so should every new player get it, or only some? Which players, how much does targeting gain, and how sure can we be with the data one experiment gives us?
#
# **Milestone.** M10 · **Theory notes:** [hte](../docs/theory/hte.md), [causal-forests](../docs/theory/causal-forests.md), [policy-learning](../docs/theory/policy-learning.md), [metalearners](../docs/theory/metalearners.md)
#
# ## Where we are
#
# Notebook 06 showed that at the Small preset (+2 points on average) the bonus earns only about 0.7¢ per player once its cost is paid, and that 30,000 players cannot even show it pays. But the lift is not the same for everyone: the simulator gives tier 3 countries 1.5× the average lift and paid social 1.25× (DECISIONS.md), and the cost is not the same either. This notebook does what the brief asks for after the ship decision: **policy learning, done once on the final sample**, with the safeguards of brief §8 (covariates fixed in advance, honest sample splitting, an overall test before any segment is shown, and a plain subgroup comparison the forest has to beat). On simulated data the truth is known, so every rule is scored against it.

# %% [markdown]
# ## 1. Model
#
# ### Who is worth a bonus
#
# For a player with sign-up attributes $x$, the conditional average treatment effect (CATE) is
#
# $$
# \tau(x) = \mathbb E\,[\,Y(1) - Y(0) \mid X = x\,],
# $$
#
# the lift in the chance of reaching level 5. Giving that player the Starter Bonus changes value by the same economics as the guardrail (notebook 06): extra activations are worth $V$, and each activated bonus player costs $c$ (the 40 coins paid early to those who would never reach level 10):
#
# $$
# G(x) = (V - c)\,\tau(x) - c\,p_0(x), \qquad p_0(x) = \Pr[\,Y(0) = 1 \mid X = x\,].
# $$
#
# So each player has a **personal break-even**: give the bonus when
#
# $$
# \tau(x) > \tau^\star(x) = \frac{c\,p_0(x)}{V - c}.
# $$
#
# Two things make a player a good target: a large lift, and a low baseline (fewer bonuses paid to players who would have activated anyway). $p_0(x)$ comes from the CUPAC model of notebook 06, trained on an earlier cohort and computed at sign-up, so the rule can be applied to every new player.
#
# ### The value of a targeting rule
#
# A rule $\pi(x) \in \{0, 1\}$ says who gets the bonus. Its value per player, relative to giving no one the bonus, is
#
# $$
# \Pi(\pi) = \mathbb E\,[\,\pi(X)\,G(X)\,].
# $$
#
# "Treat all" is $\pi \equiv 1$; the best possible rule on $x$ is $\pi^\star(x) = \mathbb 1\{G(x) > 0\}$ (Wager, *Causal Inference*, Prop. 4.1). The **gain from targeting** is $\Pi(\hat\pi) - \Pi(1)$.
#
# ### The causal forest
#
# `econml`'s `CausalForestDML` fits $\tau(x)$ by the R-learner: residualise the outcome and the arm on everything known at sign-up (cross-fitted), then grow **honest** trees, where one half of each subsample places the splits and the other half estimates the leaf effects:
#
# $$
# \hat\tau = \arg\min_{\tau(\cdot)} \sum_i \Big( \big(Y_i - \hat\ell(X_i, W_i)\big) - \tau(X_i)\,\big(T_i - \tfrac12\big) \Big)^2 .
# $$
#
# Effects vary over the pre-specified attributes $X$ (country tier, device, channel, evening sign-up). The pre-sign-up signals enter only as a control $W$ (the CUPAC score), which sharpens the residuals without being searched for heterogeneity.
#
# ### Honest checks on a held-out half
#
# The final sample is split in two at random. Half **A** fits the forest and the subgroup rule; half **B** only judges them. On B each player gets a doubly robust score, with the known assignment probability $e = \tfrac12$:
#
# $$
# \Gamma_i = \hat\mu_1 - \hat\mu_0 + \frac{T_i\,(Y_i - \hat\mu_1)}{1/2} - \frac{(1 - T_i)(Y_i - \hat\mu_0)}{1/2},
# \qquad \hat\mu_t = \hat\mu_t(X_i, W_i)\ \text{cross-fitted on B}.
# $$
#
# - **Is there heterogeneity at all?** Before any segment is shown, two tests. A pre-specified one on the whole sample: an OLS of $Y$ on the arm, the segments and their interactions, with a joint Wald test that the interactions are zero. And the forest's own calibration test on B (Chernozhukov et al. 2018, the "best linear predictor"): regress $\Gamma_i = \alpha + \beta\,(\hat\tau(X_i) - \bar{\hat\tau}) + \varepsilon_i$. A slope $\beta$ clearly above 0 means the differences the forest found on A are real on B.
# - **What does a rule earn?** $\hat\Pi(\pi) = \frac{1}{|B|}\sum_{i\in B} \pi(X_i)\,\hat G_i$, with $\hat G_i = (V - c)\,\Gamma_i - c\,\Gamma^0_i$ and $\Gamma^0_i = \hat\mu_0 + (1 - T_i)(Y_i - \hat\mu_0)/\tfrac12$.
#
# ### The baselines the forest has to beat
#
# - **Subgroups.** Nine pre-specified subgroups (country tier × channel), each with its own average effect (group average treatment effects, GATEs, from `doubleml`) and control rate. Give the bonus to a whole subgroup when its estimated $G$ is positive.
# - **Average lift, personal baseline.** $G(x)$ has two parts, and only the first needs heterogeneity. Assume everyone gets the average lift $\bar\tau$ (the CUPAC estimate from half A) and target on cost alone:
#
# $$
# \pi_{\text{base}}(x) = \mathbb 1\Big\{\bar\tau > \frac{c\,\hat p_0(x)}{V - c}\Big\}.
# $$
#
#   This needs no search for segments, only the average the test already measured and the CUPAC score. It is right if the lift does not shrink for players with a low baseline, which the experiment can check (an interaction of the arm with the score).

# %% [markdown]
# ## 2. Libraries
#
# | Library | Used for |
# |---|---|
# | `econml` | `CausalForestDML` (honest causal forest, R-learner); `DRTester` (calibration test and targeting curve on the held-out half); `SingleTreePolicyInterpreter` (a shallow tree to read the rule) |
# | `doubleml` | `DoubleMLIRM` and `.gate()`: subgroup effects for the baseline rule, with joint intervals |
# | `statsmodels` | OLS with interactions and a joint Wald test (the pre-specified heterogeneity test) |
# | `scikit-learn` | Nuisance models (gradient boosting; a constant propensity of 1/2, since assignment is a fair coin) and cross-fitting for the doubly robust scores |
# | `ablab` | Simulator, CUPAC model, guardrail economics |
# | `numpy`, `pandas`, `matplotlib`, `seaborn` | Tables and figures |
#
# Written here: the doubly robust policy value (one line on top of cross-fitted predictions) and the scoring of each rule against the simulator's truth.

# %%
import json
import time
import warnings
from pathlib import Path

import doubleml as dml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from econml.cate_interpreter import SingleTreePolicyInterpreter
from econml.dml import CausalForestDML
from econml.validate import DRTester
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import KFold

from ablab import cupac, guardrail
from ablab.config import load
from ablab.simulator import simulate
from ablab.viz import use_style, savefig, CONTROL, TREAT, INK, MUTED

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
use_style()
pd.set_option("display.precision", 4)
CFG = load()
PLAN = CFG["plan"]
V = PLAN["value_per_activation_usd"]
COST = guardrail.extra_cost(PLAN)                     # $0.18 per activated Starter Bonus player
LIFT = CFG["presets"]["lifts"][CFG["presets"]["names"].index("Small real effect")]   # +2 points
N_FINAL = PLAN["max_players"]                      # the final sample: the planned maximum, 30,000
MODEL = cupac.load()
TIERS, CHANNELS = CFG["covariates"]["tier"]["levels"], CFG["covariates"]["channel"]["levels"]
SEED = 20261022
print(f"seed {SEED}; true average lift +{LIFT * 100:.0f} points; final sample {N_FINAL:,}; V = ${V:.2f}, c = ${COST:.2f}")

# %% [markdown]
# ## 3. Data
#
# ### The final sample
#
# One experiment at the Small preset, run to the planned maximum of 30,000 players. (A run on the page stops at its verdict, typically around 13,000–15,000 players at this preset; section 6 shows what that does to targeting.)

# %%
def features(df):
    """X: pre-specified attributes the effect may vary over. W: the CUPAC score, a control only."""
    X = pd.DataFrame({
        "tier_2": (df.tier == 1) * 1.0, "tier_3": (df.tier == 2) * 1.0,
        "android": (df.device == 1) * 1.0,
        "paid_social": (df.channel == 1) * 1.0, "referral": (df.channel == 2) * 1.0,
        "evening": df.evening * 1.0,
    }, index=df.index)
    W = pd.DataFrame({"cupac_score": cupac.score(df, MODEL)}, index=df.index)
    return X, W


def cell_of(df):
    return pd.Categorical([f"{TIERS[t]} · {CHANNELS[c]}" for t, c in zip(df.tier, df.channel)],
                          categories=[f"{t} · {c}" for t in TIERS for c in CHANNELS])


exp, _ = simulate(LIFT, seed=SEED)
exp = exp.iloc[:N_FINAL].reset_index(drop=True)
X, W = features(exp)
y, t = exp.activated.to_numpy(float), exp.treated.to_numpy(int)
rng = np.random.default_rng(SEED)
A = rng.random(len(exp)) < 0.5        # honest split: A fits, B judges
B = ~A
print(f"{len(exp):,} players: {A.sum():,} in half A (fit), {B.sum():,} in half B (judge); "
      f"{t.mean():.1%} on the Starter Bonus")
pd.concat([exp[["player_id", "tier", "device", "channel", "evening", "treated", "activated"]], W], axis=1).head()

# %% [markdown]
# ### The truth, for scoring
#
# A fresh population of future players (two more fortnights) with each player's true lift $\tau_i$ and true baseline $p_{0,i}$ from the simulator. Every rule learned from the experiment is applied to them and scored by its true value $\frac1N\sum_i \pi(x_i)\,\big((V - c)\tau_i - c\,p_{0,i}\big)$.

# %%
pop = pd.concat([simulate(LIFT, seed=SEED + 1 + k)[0] for k in range(2)], ignore_index=True)
Xp, Wp = features(pop)
P0_HAT = Wp.cupac_score.to_numpy()                       # what a rule can know at sign-up
TRUE_G = guardrail.value_from_lift(pop.tau.to_numpy(), pop.p0.to_numpy(), PLAN)   # true value of a bonus, per player
COST_IN_LIFT = COST * P0_HAT / (V - COST)                      # personal break-even tau*(x), from the CUPAC score
pop_cell = cell_of(pop)


def true_value(treat):
    """True value per player of a rule, relative to no bonus (cents)."""
    return 100 * float(np.mean(np.where(treat, TRUE_G, 0.0)))


print(f"population {len(pop):,}; treat-all value {true_value(np.ones(len(pop), bool)):.2f}¢ per player")

# %% [markdown]
# ## 4. Descriptives
#
# ### Where the bonus pays, in truth
#
# By country tier × channel: the true lift, the average break-even of the players in that cell, and the true value of giving them the bonus.

# %%
truth = (pd.DataFrame({"cell": pop_cell, "tau": pop.tau, "p0": pop.p0, "be": COST * pop.p0 / (V - COST), "G": TRUE_G})
         .groupby("cell", observed=True)
         .agg(share=("tau", "size"), true_lift=("tau", "mean"), baseline=("p0", "mean"),
              break_even=("be", "mean"), value_cents=("G", "mean")))
truth["share"] /= len(pop)
truth["value_cents"] *= 100
truth["pays"] = truth.value_cents > 0
truth.sort_values("value_cents", ascending=False).round(4)

# %%
treat_cells_true = truth.index[truth.pays]
print(f"In truth the bonus pays in {len(treat_cells_true)} of 9 cells, "
      f"{truth.loc[treat_cells_true, 'share'].sum():.0%} of players.")
print(f"Best rule by cell: {true_value(np.isin(pop_cell, treat_cells_true)):.2f}¢; "
      f"best rule using each player's true lift and baseline: {true_value(TRUE_G > 0):.2f}¢; "
      f"treat all: {true_value(np.ones(len(pop), bool)):.2f}¢ per player")

# %% [markdown]
# ### What the experiment sees
#
# The raw difference in activation by cell, with its usual standard error. With about 3,300 players per cell the noise (±2–4 points) is as large as the differences we are looking for.

# %%
exp_cell = cell_of(exp)
raw = (pd.DataFrame({"cell": exp_cell, "y": y, "t": t}).groupby(["cell", "t"], observed=True).y
       .agg(["mean", "size", "var"]).unstack())
raw_diff = pd.DataFrame({
    "players": raw["size"].sum(axis=1),
    "control rate": raw["mean"][0],
    "difference": raw["mean"][1] - raw["mean"][0],
    "se": np.sqrt(raw["var"][1] / raw["size"][1] + raw["var"][0] / raw["size"][0]),
    "true lift": truth.true_lift,
})
raw_diff.round(4)

# %% [markdown]
# ## 5. Analysis
#
# ### Step 1: is there any heterogeneity? (pre-specified test, whole sample)

# %%
d = exp.assign(y=y, t=t)
ols = smf.ols("y ~ t * (C(tier) + C(channel) + C(device))", d).fit(cov_type="HC2")
inter = [n for n in ols.params.index if n.startswith("t:")]
wald = ols.wald_test(", ".join(f"{n} = 0" for n in inter), scalar=True)
print(f"Joint test that the lift is the same in every tier, channel and device: "
      f"chi2 = {wald.statistic:.1f} on {len(inter)} df, p = {wald.pvalue:.3f}")

# %% [markdown]
# ### Step 2: the causal forest (half A)

# %%
def fit_forest(Xa, Wa, ya, ta, seed):
    cf = CausalForestDML(
        model_y=HistGradientBoostingRegressor(max_iter=100, random_state=seed),
        model_t=DummyClassifier(strategy="prior"),          # assignment is a fair coin: e = 1/2
        discrete_treatment=True, n_estimators=1000, min_samples_leaf=50, honest=True,
        cv=2, random_state=seed)
    return cf.fit(ya, ta, X=Xa.to_numpy(), W=Wa.to_numpy())


t0 = time.time()
forest = fit_forest(X[A], W[A], y[A], t[A], SEED)
print(f"forest fitted on {A.sum():,} players in {time.time() - t0:.1f} s")
tau_hat = forest.effect(X.to_numpy())
importance = pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False)
importance.round(3).to_frame("share of splits (importance)")

# %% [markdown]
# ### Step 3: does the forest's heterogeneity hold up on half B?

# %%
tester = DRTester(model_regression=HistGradientBoostingClassifier(max_iter=100, random_state=SEED),
                  model_propensity=DummyClassifier(strategy="prior"), cate=forest, cv=2)
tester.fit_nuisance(X[B].to_numpy(), t[B], y[B], X[A].to_numpy(), t[A], y[A])
np.random.seed(SEED)                   # DRTester bootstraps with numpy's global generator
blp = tester.evaluate_blp(X[B].to_numpy(), X[A].to_numpy())
toc = tester.evaluate_uplift(X[B].to_numpy(), X[A].to_numpy(), metric="toc")
print(f"Calibration slope beta = {blp.params[0]:.2f} (se {blp.errs[0]:.2f}, p = {blp.pvals[0]:.3f}): "
      f"{'the ranking holds up on B' if blp.pvals[0] < 0.05 else 'not clearly different from no heterogeneity'}")
print(f"Targeting curve (TOC) area: {toc.params[0] * 100:.2f} points (se {toc.errs[0] * 100:.2f}, p = {toc.pvals[0]:.3f})")

# %% [markdown]
# ### Step 4: the subgroup baseline (DoubleML GATEs, half A)

# %%
def fit_gates(df_a, Xa, Wa, ya, ta, seed):
    data = dml.DoubleMLData(pd.concat([Xa, Wa], axis=1).reset_index(drop=True).assign(y=ya, t=ta),
                            "y", "t", x_cols=list(Xa.columns) + list(Wa.columns))
    irm = dml.DoubleMLIRM(data, ml_g=HistGradientBoostingClassifier(max_iter=100, random_state=seed),
                          ml_m=DummyClassifier(strategy="prior"), n_folds=2)
    np.random.seed(seed)                       # doubleml draws its folds with numpy's global generator
    irm.fit()
    groups = pd.get_dummies(pd.Series(cell_of(df_a)), dtype=bool)
    gate = irm.gate(groups=groups)
    ci = gate.confint(level=0.95, joint=True, n_rep_boot=2000)
    ci.index = groups.columns
    control = pd.Series(ya[ta == 0]).groupby(np.asarray(cell_of(df_a))[ta == 0]).mean()
    out = ci.rename(columns={"effect": "gate", "2.5 %": "lo", "97.5 %": "hi"})
    out["control_rate"] = control.reindex(out.index)
    out["value_cents"] = 100 * guardrail.value_from_lift(out.gate, out.control_rate, PLAN)
    return out


np.random.seed(SEED)
gates = fit_gates(exp[A], X[A], W[A], y[A], t[A], SEED)
gates = gates.join(truth[["true_lift"]])
gates.round(4)

# %% [markdown]
# ### Step 5: the rules, scored

# %%
def average_lift(df_a, ya, ta):
    """CUPAC-adjusted difference in means (notebook 06) on half A."""
    adj = cupac.adjusted(ya, cupac.score(df_a, MODEL), MODEL)
    return adj[ta == 1].mean() - adj[ta == 0].mean()


def rules_for(forest_, gates_, ate_):
    treat_cells = gates_.index[gates_.value_cents > 0]
    return {
        "No one": np.zeros(len(pop), bool),
        "Everyone": np.ones(len(pop), bool),
        "Subgroups (tier × channel)": np.isin(pop_cell, treat_cells),
        "Average lift, personal baseline": ate_ > COST_IN_LIFT,
        "Causal forest": forest_.effect(Xp.to_numpy()) > COST_IN_LIFT,
    }


def dr_scores(Xb, Wb, yb, tb, seed):
    """Doubly robust scores on half B: Gamma (lift) and Gamma0 (control rate), e = 1/2 known."""
    Z = pd.concat([Xb, Wb], axis=1).reset_index(drop=True)
    clf = HistGradientBoostingClassifier(max_iter=100, random_state=seed)
    mu = {0: np.zeros(len(Z)), 1: np.zeros(len(Z))}
    # cross-fit: each fold is predicted by a model trained on the other, with the arm as a feature
    for train, test in KFold(2, shuffle=True, random_state=seed).split(Z):
        m = clf.fit(Z.iloc[train].assign(t=tb[train]), yb[train])
        for arm in (0, 1):
            mu[arm][test] = m.predict_proba(Z.iloc[test].assign(t=arm))[:, 1]
    g1 = mu[1] + tb * (yb - mu[1]) / 0.5
    g0 = mu[0] + (1 - tb) * (yb - mu[0]) / 0.5
    return g1 - g0, g0


gamma, gamma0 = dr_scores(X[B], W[B], y[B], t[B], SEED)
G_hat_B = guardrail.value_from_lift(gamma, gamma0, PLAN)        # estimated value of a bonus, per player in B
ate_A = average_lift(exp[A], y[A], t[A])
print(f"average lift on half A (CUPAC): {ate_A * 100:+.2f} points")
rules = rules_for(forest, gates, ate_A)
B_cells = np.asarray(exp_cell)[B]
treat_cells_est = gates.index[gates.value_cents > 0]
B_rules = {
    "No one": np.zeros(B.sum(), bool), "Everyone": np.ones(B.sum(), bool),
    "Subgroups (tier × channel)": np.isin(B_cells, treat_cells_est),
    "Average lift, personal baseline": ate_A > COST * W.cupac_score.to_numpy()[B] / (V - COST),
    "Causal forest": tau_hat[B] > COST * W.cupac_score.to_numpy()[B] / (V - COST),
}
scores = pd.DataFrame({
    "share treated": {k: v.mean() for k, v in rules.items()},
    "estimated on B (¢/player)": {k: 100 * np.mean(np.where(v, G_hat_B, 0.0)) for k, v in B_rules.items()},
    "se on B": {k: 100 * np.std(np.where(v, G_hat_B, 0.0), ddof=1) / np.sqrt(B.sum()) for k, v in B_rules.items()},
    "true value (¢/player)": {k: true_value(v) for k, v in rules.items()},
})
scores.loc["Best rule by cell (truth)"] = [np.isin(pop_cell, treat_cells_true).mean(), np.nan, np.nan,
                                          true_value(np.isin(pop_cell, treat_cells_true))]
scores.loc["Best possible (each player's truth)"] = [(TRUE_G > 0).mean(), np.nan, np.nan, true_value(TRUE_G > 0)]
scores.round(3)

# %% [markdown]
# ### Step 5b: the assumption behind the baseline rule
#
# "Average lift, personal baseline" assumes the lift does not shrink for players unlikely to activate anyway. On the whole sample, the interaction of the arm with the centred CUPAC score:

# %%
ass = smf.ols("y ~ t * xc", exp.assign(y=y, t=t, xc=W.cupac_score - MODEL["mu"])).fit(cov_type="HC2")
lo_i, hi_i = ass.conf_int().loc["t:xc"]
print(f"lift change per +10 points of predicted baseline: {ass.params['t:xc'] * 0.1 * 100:+.2f} points "
      f"(95% interval {lo_i * 0.1 * 100:+.2f} to {hi_i * 0.1 * 100:+.2f}, p = {ass.pvalues['t:xc']:.2f})")

# %% [markdown]
# ### Step 6: the rule as a shallow tree
#
# A depth-2 tree fitted to the forest's effects, with each player's break-even as the cost of treating. This is the form a product team can read and implement.

# %%
interp = SingleTreePolicyInterpreter(max_depth=2, min_samples_leaf=500, random_state=SEED)
interp.interpret(forest, X[A].to_numpy(), sample_treatment_costs=COST * W.cupac_score.to_numpy()[A] / (V - COST))
tree_rule = interp.treat(Xp.to_numpy()) == 1


def leaf_rules(tree, names):
    """Plain-language path to each leaf of a fitted sklearn tree (binary features)."""
    tr, out = tree.tree_, {}

    def walk(node, path):
        if tr.children_left[node] == -1:
            out[node] = " and ".join(path) or "everyone"
            return
        f = names[tr.feature[node]]
        walk(tr.children_left[node], path + [f"not {f}"])
        walk(tr.children_right[node], path + [f])
    walk(0, [])
    return out


tree_model = interp.tree_model_
paths = leaf_rules(tree_model, list(X.columns))
leaf_pop, leaf_A = tree_model.apply(Xp.to_numpy()), tree_model.apply(X[A].to_numpy())
leaves = pd.DataFrame({
    "rule": paths,
    "share of players": {k: np.mean(leaf_pop == k) for k in paths},
    "forest: value of a bonus (¢/player)": {k: 100 * np.mean(guardrail.value_from_lift(tau_hat[A], W.cupac_score.to_numpy()[A], PLAN)[leaf_A == k]) for k in paths},
    "true value of a bonus (¢/player)": {k: 100 * TRUE_G[leaf_pop == k].mean() for k in paths},
    "bonus": {k: bool(interp.treat(Xp.to_numpy()[leaf_pop == k][:1])[0] == 1) for k in paths},
}).sort_values("forest: value of a bonus (¢/player)", ascending=False)
print(f"Shallow tree: treats {tree_rule.mean():.0%} of players, true value {true_value(tree_rule):.2f}¢ per player")
leaves.round(3)

# %% [markdown]
# ## 6. Repeated experiments
#
# One experiment is one draw. The same pipeline on many independent experiments, at three sizes: 15,000 players (about where a run at this preset stops at its verdict), 30,000 (the planned maximum) and the whole 14 days (about 100,000). Each repetition re-fits everything on its own half A, estimates on its own half B, and is scored against the truth. Cached in `results/08_targeting.json`.

# %%
def one_experiment(n, seed):
    df, _ = simulate(LIFT, seed=seed)
    df = df.iloc[:n].reset_index(drop=True)
    Xr, Wr = features(df)
    yr, tr = df.activated.to_numpy(float), df.treated.to_numpy(int)
    Ar = np.random.default_rng(seed).random(len(df)) < 0.5
    olsr = smf.ols("y ~ t * (C(tier) + C(channel) + C(device))", df.assign(y=yr, t=tr)).fit(cov_type="HC2")
    names = [k for k in olsr.params.index if k.startswith("t:")]
    p_inter = float(olsr.wald_test(", ".join(f"{k} = 0" for k in names), scalar=True).pvalue)
    f = fit_forest(Xr[Ar], Wr[Ar], yr[Ar], tr[Ar], seed)
    te = DRTester(model_regression=HistGradientBoostingClassifier(max_iter=100, random_state=seed),
                  model_propensity=DummyClassifier(strategy="prior"), cate=f, cv=2)
    te.fit_nuisance(Xr[~Ar].to_numpy(), tr[~Ar], yr[~Ar], Xr[Ar].to_numpy(), tr[Ar], yr[Ar])
    b = te.evaluate_blp(Xr[~Ar].to_numpy(), Xr[Ar].to_numpy())
    np.random.seed(seed)
    g = fit_gates(df[Ar], Xr[Ar], Wr[Ar], yr[Ar], tr[Ar], seed)
    ate = average_lift(df[Ar], yr[Ar], tr[Ar])
    rr = rules_for(f, g, ate)
    gam, gam0 = dr_scores(Xr[~Ar], Wr[~Ar], yr[~Ar], tr[~Ar], seed)
    Gb = guardrail.value_from_lift(gam, gam0, PLAN)
    forest_b = f.effect(Xr[~Ar].to_numpy()) > COST * Wr.cupac_score.to_numpy()[~Ar] / (V - COST)
    return {
        "n": n, "seed": seed, "p_interactions": p_inter, "blp_slope": float(b.params[0]), "p_blp": float(b.pvals[0]),
        "true_all": true_value(rr["Everyone"]), "true_subgroups": true_value(rr["Subgroups (tier × channel)"]),
        "true_forest": true_value(rr["Causal forest"]), "share_forest": float(rr["Causal forest"].mean()),
        "true_baseline_rule": true_value(rr["Average lift, personal baseline"]),
        "share_baseline_rule": float(rr["Average lift, personal baseline"].mean()), "ate_A": float(ate),
        "est_forest_gain": 100 * float(np.mean(np.where(forest_b, Gb, 0.0)) - np.mean(Gb)),
        "true_forest_gain": true_value(rr["Causal forest"]) - true_value(rr["Everyone"]),
    }


CACHE = Path("../results/08_targeting.json")
SIZES, REPS = [15_000, 30_000, 100_000], 25
key = {"seed": SEED, "lift": LIFT, "cupac_theta": MODEL["theta"], "version": 2}   # 2: adds the baseline rule
cached = json.loads(CACHE.read_text()) if CACHE.exists() else {}
rows = cached.get("rows", []) if cached.get("key") == key else []
done = {(r["n"], r["seed"]) for r in rows}
todo = [(n, SEED + 1000 * (i + 1) + r) for i, n in enumerate(SIZES) for r in range(REPS)]
t0 = time.time()
for j, (n, seed) in enumerate([x for x in todo if x not in done]):
    rows.append(one_experiment(n, seed))
    CACHE.write_text(json.dumps({"key": key, "rows": rows}, indent=1))   # saved after each experiment
    print(f"  {j + 1} new, n = {n:,}, {(time.time() - t0) / 60:.1f} min", flush=True)
rep = pd.DataFrame([r for r in rows if (r["n"], r["seed"]) in set(todo)])
print(f"{len(rep)} experiments ({len(todo) - len(done & set(todo))} run now, the rest from {CACHE.name})")

summary = rep.groupby("n").agg(
    treat_all=("true_all", "mean"), subgroups=("true_subgroups", "mean"),
    baseline_rule=("true_baseline_rule", "mean"), forest=("true_forest", "mean"),
    subgroups_sd=("true_subgroups", "std"), baseline_rule_sd=("true_baseline_rule", "std"), forest_sd=("true_forest", "std"),
    heterogeneity_found_ols=("p_interactions", lambda p: (p < 0.05).mean()),
    heterogeneity_found_forest=("p_blp", lambda p: (p < 0.05).mean()),
    blp_slope=("blp_slope", "mean"),
)
summary["forest_beats_subgroups"] = rep.assign(w=rep.true_forest > rep.true_subgroups).groupby("n").w.mean()
summary["forest_beats_baseline_rule"] = rep.assign(w=rep.true_forest > rep.true_baseline_rule).groupby("n").w.mean()
summary["forest_worse_than_all"] = rep.assign(w=rep.true_forest < rep.true_all).groupby("n").w.mean()
summary.round(3)

# %% [markdown]
# Is the held-out estimate of the gain honest? Across experiments, the gain estimated on half B against the true gain of the same rule:

# %%
honesty = rep.groupby("n").apply(lambda g: pd.Series({
    "estimated gain, mean (¢)": g.est_forest_gain.mean(), "true gain, mean (¢)": g.true_forest_gain.mean(),
    "estimate − truth, sd (¢)": (g.est_forest_gain - g.true_forest_gain).std()}), include_groups=False)
honesty.round(3)

# %% [markdown]
# ## 7. Figures


# %%
# Where the bonus pays, in truth
fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
grid = lambda col: truth[col].to_numpy().reshape(len(TIERS), len(CHANNELS))
for ax, (col, title, fmt, cmap, scale) in zip(axes, [
        ("true_lift", "True lift (points)", ".1f", "YlOrBr", 100),
        ("break_even", "Break-even lift (points)", ".1f", "Greys", 100),
        ("value_cents", "Value of a bonus (¢ per player)", "+.1f", "BrBG", 1)]):
    vals = grid(col) * scale
    labels = np.vectorize(lambda v: format(v, fmt).replace("-", "−"))(vals)
    sns.heatmap(vals, ax=ax, annot=labels, fmt="", cbar=False, cmap=cmap, linewidths=1, linecolor="white",
                center=0 if col == "value_cents" else None, xticklabels=CHANNELS, yticklabels=TIERS,
                annot_kws={"fontsize": 10})
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("")
    ax.tick_params(axis="y", rotation=0)
fig.suptitle("The bonus pays where the lift is large and the baseline low", y=1.04)
savefig(fig, "08_truth_by_cell")

# %%
# Estimated vs true effect by cell
cells = list(truth.index)
fcell = pd.Series(tau_hat[B]).groupby(np.asarray(exp_cell)[B]).mean().reindex(cells)
fig, ax = plt.subplots(figsize=(9, 4.2))
ypos = np.arange(len(cells))[::-1]
ax.hlines(ypos, gates.lo.reindex(cells) * 100, gates.hi.reindex(cells) * 100, color=CONTROL, lw=6, alpha=0.35,
          label="Subgroup effect, 95% joint interval (DoubleML)")
ax.plot(gates.gate.reindex(cells) * 100, ypos, "o", color=CONTROL, ms=6)
ax.plot(fcell * 100, ypos, "D", color=TREAT, ms=7, label="Causal forest, cell average")
ax.plot(truth.true_lift * 100, ypos, "|", color=INK, ms=18, mew=2.2, label="True lift")
ax.axvline(0, color=MUTED, ls="--", lw=1)
ax.set_yticks(ypos, cells)
ax.set_xlabel("Lift (percentage points)")
ax.set_title("From the 15,000 players of half A, every subgroup interval still includes zero", pad=34)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=3, borderaxespad=0.2, fontsize=9)
ax.grid(axis="y", visible=False)
savefig(fig, "08_estimates_vs_truth")

# %%
# Value of each rule, repeated experiments
RULE_COLS = {"true_all": "Everyone", "true_subgroups": "Subgroups", "true_baseline_rule": "Average lift, personal baseline",
             "true_forest": "Causal forest"}
PAL = {"Everyone": CONTROL, "Subgroups": "#7d8fa6", "Average lift, personal baseline": "#3f8f7a", "Causal forest": TREAT}
long = rep.melt(id_vars="n", value_vars=list(RULE_COLS), var_name="rule", value_name="value")
long["rule"] = long.rule.map(RULE_COLS)
long["size"] = long.n.map(lambda n: f"{n // 1000}k players" if n < 100_000 else "14 days (~100k)")
fig, ax = plt.subplots(figsize=(10.5, 4.4))
sns.stripplot(data=long, x="size", y="value", hue="rule", dodge=True, ax=ax, size=3.5, alpha=0.55, jitter=0.12,
              palette=PAL, legend=False)
sns.pointplot(data=long, x="size", y="value", hue="rule", dodge=0.6, ax=ax, linestyle="none", errorbar=None,
              markers="_", markersize=20, palette={k: INK for k in PAL}, legend=False)
for yv, label, ls in [(true_value(np.isin(pop_cell, treat_cells_true)), "best rule by cell", ":"),
                      (true_value(TRUE_G > 0), "best possible", "--")]:
    ax.axhline(yv, color=MUTED, ls=ls, lw=1.2)
    ax.text(2.48, yv + 0.03, label, color=MUTED, fontsize=9, ha="right")
ax.axhline(0, color=MUTED, lw=1)
ax.set_xlabel("")
ax.set_ylabel("True value per player (¢)")
ax.set_title(f"Targeting on cost beats searching for high-lift segments ({REPS} experiments per size)", pad=30)
handles = [plt.Line2D([], [], marker="o", ls="none", color=c, label=k) for k, c in PAL.items()]
ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=4, borderaxespad=0.2, fontsize=9)
ax.grid(axis="x", visible=False)
savefig(fig, "08_value_by_rule")

# %%
# Shallow tree
fig, ax = plt.subplots(figsize=(10, 0.7 + 0.62 * len(leaves)))
yl = np.arange(len(leaves))[::-1]
est, tru = leaves["forest: value of a bonus (¢/player)"], leaves["true value of a bonus (¢/player)"]
ax.barh(yl + 0.18, est, height=0.34, color=[TREAT if b else CONTROL for b in leaves.bonus], label="Forest estimate (half A)")
ax.barh(yl - 0.18, tru, height=0.34, color="none", edgecolor=INK, lw=1.2, label="Truth")
ax.axvline(0, color=MUTED, lw=1)
ax.set_yticks(yl, [f"{r.replace('_', ' ')}  ({s:.0%})" for r, s in zip(leaves.rule, leaves["share of players"])])
ax.set_xlabel("Value of a bonus (¢ per player)")
ax.set_title("The depth-2 tree from the one experiment: tier 3 is real, the evening split is noise", pad=30)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, borderaxespad=0.2, fontsize=9)
ax.grid(axis="y", visible=False)
savefig(fig, "08_policy_tree")

# %% [markdown]
# ## 8. Results

# %%
s30 = summary.loc[N_FINAL]
print(f"One experiment, 30,000 players: pre-specified test p = {wald.pvalue:.3f}; forest calibration p = {blp.pvals[0]:.3f}")
print(f"True value per player: everyone {scores.loc['Everyone', 'true value (¢/player)']:.2f}¢, "
      f"subgroups {scores.loc['Subgroups (tier × channel)', 'true value (¢/player)']:.2f}¢, "
      f"forest {scores.loc['Causal forest', 'true value (¢/player)']:.2f}¢, tree {true_value(tree_rule):.2f}¢, "
      f"best possible {true_value(TRUE_G > 0):.2f}¢")
print("Repeated experiments (mean true value, ¢ per player):")
print(summary[["treat_all", "subgroups", "baseline_rule", "forest", "forest_beats_subgroups", "forest_beats_baseline_rule",
               "heterogeneity_found_ols", "heterogeneity_found_forest", "blp_slope"]].round(3).to_string())

# %% [markdown]
# - **Targeting pays.** In truth the bonus pays in 4 of the 9 tier × channel cells (43% of players). Giving it to everyone earns 0.68¢ per player; the best rule by cell earns 1.45¢; the best possible rule, knowing each player's true lift and baseline, 2.05¢.
# - **Most of the gain is on the cost side, and it needs no search for segments.** "Average lift, personal baseline" (the average lift the test already measured, and the CUPAC score as each player's baseline) earns 1.36¢ at 15,000 players, 1.58¢ at 30,000 and 1.68¢ over 14 days, above the best rule by cell from 30,000 players on. It never did worse than treating everyone at 30,000 players or more (2 of 25 runs at 15,000, when the average lift was badly underestimated).
# - **The causal forest finds little real heterogeneity at these sizes.** Its calibration slope on the held-out half averages 0.07–0.13 (1 would mean its ranking is fully right), and the test detects heterogeneity in only 8%, 8% and 20% of runs. Its rule (0.98¢, 1.09¢, 1.32¢) does beat the subgroup rule (0.83¢, 1.01¢, 1.19¢) more often than not, but it never beat the cost-side rule at 30,000 players or more. Most of what it gains comes from the baseline term it shares with that rule.
# - **The safeguards do their job: they say "not enough evidence" most of the time.** The pre-specified interaction test finds heterogeneity in 20%, 28% and 64% of runs. Under the brief's rule (no segments shown before an overall test passes), the page would show no segment list for a typical 30,000-player run. The lift really does vary (tier 3 gets 1.5×), but one experiment of this size cannot show it reliably.
# - **The held-out estimate of the gain is honest on average but noisy.** At 30,000 players the forest's gain over treating everyone is estimated on half B at +0.50¢ on average against a true +0.41¢, but a single estimate is off by about ±0.8¢, as much as the gain itself.
# - **The one experiment above is an unlucky draw**, which is why section 6 exists. Its half A put the average lift at +0.5 points (truth +2), so every rule fitted on it treats too few players, and the forest and the cost-side rule (0.63¢ each) both fall just short of treating everyone (0.68¢). The depth-2 tree splits on tier 3, which is real, and then on evening sign-ups, which is noise.
# - **The assumption behind the cost-side rule holds here.** In the experiment the lift *grows* as the predicted baseline falls (−0.55 points per +10 points of baseline, interval −1.20 to +0.10), because in this world tier 3 has both the lowest baseline and the largest lift. In a real game the lift could instead be concentrated among engaged players with a high baseline; that interaction is the check to run before using the rule.
#
# **For the page.** The honest headline is that the targeting question is answered mostly by the economics, not by a forest: give the bonus to the players least likely to reach level 5 anyway, unless the experiment shows the lift shrinks for them. The causal forest is worth showing as the method the brief asks for, with its tests failing as often as they do. Daniel to decide what the "Ship it to whom?" section shows.

# %% [markdown]
# ## 9. What gets promoted
#
# Nothing runs in the browser: the brief rules out refitting forests on the page. The page's "Ship it to whom?" section (After tab) shows the repeated experiments and the truth by cell, precomputed, with the safeguards stated.
#
# | Item | Goes to | Guarded by |
# |---|---|---|
# | Value of a bonus per player, $G = (V - c)\tau - c\,p_0$ | already `ablab.guardrail.value_from_lift` | parity cell below |
# | Targeting results (truth by cell, rule values by size, tests) | `scripts/targeting_page.py` → `web/public/targeting.json` → `TargetingSection.svelte` | `tests/test_targeting_page.py`; parity cell below |

# %% [markdown]
# ## 10. Production parity
#
# The value of a bonus used for targeting is the guardrail's function from notebook 06, applied player by player.

# %%
tau_i, p0_i = pop.tau.to_numpy(), pop.p0.to_numpy()
assert np.allclose(TRUE_G, (V - COST) * tau_i - COST * p0_i)
assert np.allclose(truth.break_even, (COST * pop.p0 / (V - COST)).groupby(pop_cell, observed=True).mean())
assert abs(guardrail.value_from_lift(0.0, CFG["experiment"]["baseline_rate"], PLAN)
           + COST * CFG["experiment"]["baseline_rate"]) < 1e-15
print("targeting uses ablab.guardrail.value_from_lift: same economics as the page's 'Pays for itself'")

page = json.loads(Path("../web/public/targeting.json").read_text())       # scripts/targeting_page.py
page_cells = pd.DataFrame(page["truth"]["cells"]).set_index(["tier", "channel"])
for cell_name, row in truth.iterrows():
    tier_name, channel_name = cell_name.split(" · ")
    assert abs(page_cells.loc[(tier_name, channel_name), "value_cents"] - row.value_cents) < 1e-9
assert abs(page["truth"]["best_possible_cents"] - true_value(TRUE_G > 0)) < 1e-9
assert abs(page["truth"]["best_by_cell_cents"] - true_value(np.isin(pop_cell, treat_cells_true))) < 1e-9
print("web/public/targeting.json reproduces this notebook's truth and repeated experiments")
