# Library review

2026-10-12. Which established Python libraries should replace hand-written code, and where hand-written code has to stay.

Each library was installed in a scratch Python 3.11 environment on this machine and tried on our own numbers (the notebook 01 run: 50,458 / 11,146 control, 50,169 / 11,929 treatment).

## The rule

- **Notebooks and the Python reference use established libraries wherever one fits.** That is what a reviewer expects to see, and it means our numbers are checked against code that thousands of people use.
- **The browser engine is necessarily our own code.** The live page has no Python, so every formula it runs is ported by hand. That port is checked against the *library* results, not against more hand-written Python.
- **The config and the JSON fixtures don't change.** Libraries are used to compute and verify the numbers; the files the browser reads stay plain TOML and JSON.

## Verdicts

| Library | Version tried | Use it for | Verdict |
|---|---|---|---|
| **mmh3** | 5.3.1 | Hash assignment | **Adopt.** Replaces our hand-written MurmurHash3. Becomes a core dependency. It also generates the fixtures the browser hash must match. |
| **statsmodels** | 0.15.0 | Naive diff in proportions, logit check of the DGP, OLS with robust SEs | **Adopt.** `confint_proportions_2indep` and `test_proportions_2indep` work straight from counts, so they fit running totals. On our run: diff +1.69 points, 95% CI [1.17, 2.21], p = 1.9e-10. |
| **scipy.stats** | 1.17 | SRM χ², distributions | **Adopt** (already a dependency). `chisquare([n_c, n_t])` gives p = 0.36 on our run. |
| **seaborn** | 0.13.2 | Heatmaps, histograms, distributions | **Adopt** for notebooks. Replaces hand-annotated `imshow` and manual histogram overlays. Keeps our matplotlib style. |
| **causalml** | 0.17.0 | `causalml.match.create_table_one`: balance table with SMD | **Adopt** for notebooks (Daniel's pick, replacing `tableone`). Works on numeric columns, so categories become 0/1 indicators and each level gets its own SMD. |
| **gbstats** | 0.8.0 | GrowthBook's open-source stats engine: `SequentialTwoSidedTTest` (Waudby-Smith asymptotic CS, from summary statistics) | **Adopt as the reference** for our confidence sequence. Same formula and same ρ tuning as ours; matches our interval to every printed digit on the notebook 01 run. It pins `pandas<2`, so it is installed separately with `--no-deps` (plus `pydantic`); it runs fine on pandas 3. |
| **savvi** | 0.3.1 | Always-valid SRM test (Lindon & Malek 2022); always-valid regression adjustment (Lindon et al.) | **Adopt as a reference** for M9 and the SRM check. See note below. |
| **econml** | 0.17.0 | `CausalForestDML` for the targeting article | **Adopt** (M10, `article` extra). Already planned. |
| **doubleml** | 0.11.4 | Group average treatment effects (`gate`), policy trees | **Adopt** (M10). Gives the pre-specified subgroup baseline the brief asks the forest to beat. |
| **pymc / bambi** | 5.28 / 0.17 | Bayesian models | **Optional** (M10 only). A hierarchical model of segment effects with partial pooling would be a nice companion to the forest. Not needed for the live engine: a Bayesian A/B on a yes/no metric is a closed-form Beta–Binomial in `scipy.stats.beta`. |
| **pyfixest** | 0.60.0 | Fast fixed-effects regression, robust and clustered SEs | **Skip for now.** Excellent, but we run single regressions with no fixed effects or clusters; statsmodels covers it. |
| **spotify-confidence** | 4.1.0 | Z-tests from summary statistics, group-sequential tests | **Skip.** Works (identical numbers to statsmodels), but its sequential method is group-sequential with alpha spending, not an always-valid interval. It also pulls in heavy plotting dependencies. |
| **confseq** | 0.0.11 | Howard et al. boundaries | **Not usable.** The build fails on Windows / Python 3.11 (needs a C++ compiler and Boost). The PyPI page calls it early-stage and tests only up to Python 3.10. |

## The always-valid interval: ours in the browser, gbstats as the reference

*Corrected 2026-10-12.* The first version of this review said no installable library fits. That was wrong: GrowthBook's stats engine, **gbstats**, is open source on PyPI and implements exactly our method.

- **gbstats** (`gbstats.frequentist.tests.SequentialTwoSidedTTest`): the Waudby-Smith et al. asymptotic confidence sequence, from per-arm summary statistics, with ρ tuned to a planned sample size N* (eq. 161 of the paper) and the matching p-value (eq. 155). On the notebook 01 run with N* = 12,000 it gives [0.00835, 0.02541], identical to our formula.
- **Statsig** uses an mSPRT with a normal mixing variance τ; its interval is the same family, with τ in the role of our ρ². Its engine is not open source.
- Other open-source options exist but don't fit as well: **confseq** (the authors' own library; fails to build here), **savvi** and **avinf** (anytime-valid regression; a different construction), and the R packages **avlm** and **safestats**.

So the Python side calls a library after all. The browser still needs its own port, because there is no Python on the page. The plan becomes:

1. The Python reference is checked against **gbstats** on shared fixtures (interval and p-value).
2. The browser port is checked against the same fixtures (validity evidence 4).
3. Simulations check false alarms and coverage (validity evidence 1–3).

One difference to handle: gbstats reports the p-value at the current look, 1/Λₙ. An always-valid p-value should never go back up, so ours takes the running minimum over looks. Same number at any look where it is at its lowest; ours is the safer one to display.

## savvi note

savvi gives an always-valid SRM test. That matters because the page checks the split on every refresh: a plain χ² checked every refresh raises false alarms for the same reason the naive interval does. The cost is that savvi is slow (it runs per update), and the browser still needs a hand port: a Dirichlet–multinomial Bayes factor, which is closed form with log-gamma.

Proposal: use savvi as the Python reference for the SRM check, and port the formula. This tightens an item already in scope rather than adding one.

**Quick test (scratch script, 300 runs with no real imbalance, 100 hourly checks of about 300 players each):**

| Check run every hour | Runs that falsely flagged a broken split |
|---|---|
| χ² test at 5% | **38.7%** (simulation error about ±2.8 points) |
| savvi always-valid test at 5% | **2.3%** (about ±0.9 points) |

With a genuinely broken 52 / 48 split, savvi flagged it at hour 26. savvi solves a small optimisation problem on every update (via cvxpy), which is why it is slow; the browser port will use the closed-form part only. This test becomes a proper, seeded validity check in notebook 05.

## What changes in notebook 01

| Was hand-written | Now |
|---|---|
| `murmur3_32` | `mmh3.hash(key, signed=False)` |
| `balance_table` | `causalml.match.create_table_one` |
| Heatmaps with manual annotation | `seaborn.heatmap(annot=True)` |
| Overlaid histograms | `seaborn.histplot(element="step", log_scale=True)` |
| Treatment share only | plus `scipy.stats.chisquare` SRM p-value |
| (nothing) | **New check:** fit a `statsmodels` logit to the control arm and recover the coefficients we put into the config |

The data-generating process itself stays plain numpy. That is normal: the generators in doubleml and econml produce generic continuous covariates, not sign-up hours, hashes and segments. Writing your own DGP is what researchers do, and the logit recovery check shows ours does what it says.

## Sources

- confseq on PyPI: https://pypi.org/project/confseq/
- savvi on PyPI: https://pypi.org/project/savvi
- GrowthBook sequential testing: https://docs.growthbook.io/statistics/sequential.md
- Statsig sequential testing: https://docs.statsig.com/experiments/advanced-setup/sequential-testing
- Optional stopping in Bayesian testing (Deng, Lu, Chen 2016): https://arxiv.org/pdf/1602.05549
