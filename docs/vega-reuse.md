# Vega and Lyra reuse report

Milestone 0. Written 2026-10-11 after a read-only pass over `../Vega` and `../Vega/lyra`. Nothing in either folder was changed.

**Summary.** The useful inheritance is small and good: one tested always-valid confidence sequence, its peeking simulation, the SRM test, the hash-assignment pattern, the ship rule with guardrails, and a solid shelf of theory notes. Everything is copied in, never imported. The interface, platform layer and data pipeline stay behind. Several things the brief needs do not exist anywhere yet. The biggest gaps are an always-valid p-value, a coverage-at-every-look test, a balance table, segment widening, any JS port with parity tests, and the whole persona pipeline.

---

## 1. Lyra (`Vega/lyra/`)

A Python package of 25 files (about 1,650 lines): the inference layer of the "Lyra platform". It has no tests of its own (they live in `Vega/tests/`), no JS, no UI and no LLM code.

### Reuse as-is (copy, then add our own tests)

| What | Path | Why it fits |
|---|---|---|
| `cs_multiplier(n, alpha, rho2)` | `lyra/sequential.py` | Normal-mixture asymptotic confidence sequence (Howard et al. / Waudby-Smith), written as a multiplier on the SE. Pure `math`. Needs only `n`, the estimate and its SE, so it works from running totals. |
| `advisory(...)` state logic | `lyra/sequential.py` | Maps directly to *Keep collecting / Ship / Don't ship*: stop only when the CS excludes 0, plus a minimum-runtime guard. |
| `srm_chi2(counts, allocations)` | `lyra/diagnostics.py` | Pearson χ² from counts. Two arms means df = 1, so the browser needs only the normal CDF. |
| `superior`, `non_inferior`, `ship_decision` | `lyra/decisions.py` | A conjunctive rule: primary metric superior **and** guardrail non-inferior. Exactly brief §2. Used in M9. |
| `ProportionMetric` / `MeanMetric` formulas | `lyra/metrics.py` | Unpooled two-proportion z, and the Welch-style z for the guardrail. Textbook-correct. |
| `HeteroDGP` (known τ(x)) | `lyra/dgp/hetero.py` | Truth-known reference for the targeting article (M10). |

### Adapt

| What | Path | Change needed |
|---|---|---|
| `confidence_sequence(looks)` | `lyra/sequential.py` | Drop the `n = r.get("n") or r.get("day")` fallback (using the day number as n is wrong). Compute the SE from per-arm running totals. |
| `rho2 = 0.05` default | `lyra/sequential.py` | Fixed and far from optimal: the recorded false-alarm rate is 0.5–0.7% against a 5% target, so we lose power. Tune ρ² to the planned maximum sample (Howard's ρ for a target n). |
| `CupedMetric` | `lyra/metrics.py` | Raw arrays with a pooled θ. Rewrite from sums (Σx, Σy, Σxy, Σx², Σy²), and consider the Lin (2013) interacted version. M9. |
| `ABDGP`, `PrePostDGP` | `lyra/dgp/ab.py`, `lyra/dgp/outcomes.py` | Good shape (`sample(n, seed)`, `ground_truth()`), but assignment is `rng.random() >= q`, not a hash. We need covariates with designed-in segment lift (brief §4). |
| `CausalForest`, `dr_scores`, `rate`, `uplift_curve` | `lyra/cate.py`, `lyra/policy.py` | Offline only, for the M10 article. Add honest splitting, an overall heterogeneity test, and the pre-specified subgroup baseline (brief §8). |

### Leave behind

- The platform layer: Estimator/DGP Protocol registry, lifecycle states, "certified" badges.
- Switchback, interference, panel, OPE, observational/DML and incrementality modules. Out of scope.
- Hidden heavy dependencies: statsmodels is imported but not declared. Nothing that must be ported to JS may depend on statsmodels, sklearn or econml.

## 2. Vega (`Vega/`, excluding `lyra/`)

A larger repo: an agent-based marketplace simulator, a FastAPI "chassis", a dbt/duckdb metrics layer, a React frontend, Quarto docs and a paper library. It also holds the tests for Lyra.

### Reuse as-is

| What | Path | Why it fits |
|---|---|---|
| `accrue()` running-totals simulator | `tests/test_sequential.py` | Binomial batches per look with cumulative counts. This is the seed of our validity harness. |
| Peeking simulation | `notebooks/07_sequential.py` | Recorded result (R = 2,000, 40 looks, p₀ = 0.20): naive false-alarm rate **30.4%**, confidence sequence **0.7%**. Template for the M1 validity script. Our own numbers will be produced fresh, not copied. |
| SRM / A/A tests | `tests/test_sequential.py`, `tests/test_aa_null.py` | Patterns for unit tests: 5000/5000 passes, 5400/4600 flags. |
| Named seeded RNG streams | `engine/config.py` | `SeedSequence(seed).spawn(k)` → one `default_rng` per stream (arrivals, covariates, outcomes). Copy the pattern. |
| `normCdf`, `normPpf` | `frontend/src/power.js` | JS normal CDF and quantile. erf error is about 1.5e-7, so parity tolerances must allow for it, or we switch to a more precise erfc. |
| Theory notes | see §3 | Recycled into a short "Why it's safe to peek" companion text. |

### Adapt

| What | Path | Change needed |
|---|---|---|
| Hash assignment `bucket()` / `_uniform_hash()` | `chassis/assignment.py` (SHA-256), `engine/experiments.py` (blake2b) | Same idea, `hash(player_id + experiment_key) → [0,1)`, but the browser has no synchronous SHA-256 or blake2b. Swap to a small hash that is identical in Python and TS (MurmurHash3 x86_32), with a parity test. |
| Effect-over-time chart | `frontend/src/Scorecard.jsx` (`Running`) | Right idea: CS band, fixed-CI band, point line, zero line, truth line. Rebuild as plain SVG in our own visual style; no Recharts. |
| `CIBar` | `frontend/src/ui.jsx` | Horizontal interval bar with zero line and truth tick. Re-draw for the Confidence-style rows in "details". |
| `Effect` result dataclass | `inference/base.py` | Mirror the shape (`point, ci_low, ci_high, se, n_t, n_c, p, covers(truth)`), adding the always-valid fields. |
| CUPED | `inference/cuped.py` | Same as Lyra's version: raw arrays, so rewrite from sums. |

### Leave behind

- **The scorecard timeseries** (`chassis/scorecard.py`). It re-samples a fresh dataset every day (`dgp.sample(d*npd, seed=seed0+d)`), so its looks are independent rather than one cumulative stream, and its ship decision uses the fixed-horizon CI. Neither may carry over.
- The duplicated `inference/anytime_valid.py`. Keep one implementation.
- The agent-based engine (`engine/*`), duckdb, parquet event logs, dbt, FastAPI chassis, Docker, Vercel config, Criteo validation, `labs/`.
- The tiny LCG in `frontend/src/dgpViz.js`. It is not a statistically adequate generator.
- **The whole interface**: sidebar with 5+ sections, creation wizard, registry, many stacked cards per screen, three typefaces, chips and badges and tooltips everywhere. That density is what makes Lyra hard to navigate.

## 3. Theory to recycle

| Source | Use |
|---|---|
| `Vega/paper-library/notation/anytime-valid.md` | Best single note: peeking, always-valid p-value, mSPRT mixture, Howard boundary, method comparison. Basis of the companion text. |
| `Vega/docs/sequential.qmd` | Polished chapter (Ville's inequality, peeking tax). Two errors to fix if reused: it documents an `asymptotic_cs(...)` API that does not exist, and it says the band grows like log log n (this boundary grows like √log n). |
| `Vega/paper-library/notation/causal-forests.md`, `policy-learning.md`, `hte.md` | M10 targeting article. |
| `Vega/notebooks/09_cate.py`, `10_policy.py` | Worked causal-forest and policy examples. |
| `Vega/paper-library/md/` (Johari 2017, Howard 2022, CUPED 2013, Spotify sequential series) | References for the "Methods" footnotes. |

## 4. What exists nowhere yet (we build it)

1. **Always-valid p-value.** Comes free from the same normal mixture (see §6).
2. **Coverage at every look** across many runs. Only fixed-n coverage was ever tested.
3. A validity test with the brief's thresholds. Vega's asserts only "CS FPR < 10%, naive > 15%" on 600 runs; we need ≤ 5% on ≥ 2,000 runs.
4. Covariate balance table.
5. Segment intervals with multiplicity widening.
6. Any JS port of the statistics, any parity test, and any JS test runner.
7. A real tick stream: Poisson batches, 72-hour maturity, seed in the URL.
8. The LLM persona pipeline. None of the "persona" hits in Vega are related.

## 5. Stacks

| | Vega / Lyra | Proposed for Live A/B Lab |
|---|---|---|
| Python | 3.11+, setuptools, numpy, pandas, scipy, statsmodels (undeclared), duckdb, dbt, econml | 3.11+, managed with **uv**. Engine uses only numpy and scipy. econml, scikit-learn and matplotlib only in an `article` extra (M10). Anthropic SDK only in a `personas` extra (M7). |
| Python tests | pytest, ruff | pytest, ruff, plus a `validity/` script that writes JSON results the page can cite. |
| Frontend | React 18 + Vite 5 + Recharts + KaTeX, plain JSX, no tests | **Vite + TypeScript + Svelte 5**: small runtime, built-in transitions suit the dot and band motion, and it does not resemble Vega. Charts drawn as hand-made SVG; no chart library. |
| JS tests | none | **Vitest**, with shared JSON fixtures generated by Python for parity (evidence 4). |
| RNG | numpy `default_rng` / LCG | `xoshiro128**` seeded by `splitmix32`: 32-bit operations only, identical in TS and Python. numpy stays for bulk validity sims. |
| Hash | SHA-256 / blake2b | MurmurHash3 x86_32 on `player_id:experiment_key`, ÷ 2³². |
| Docs | Quarto sites | Markdown in `docs/`. The targeting article is one notebook rendered to a page. |
| Deploy | FastAPI + Vercel + Docker | Static `dist/` only. Host still open (DECISIONS #7). |

The page is one screen with a few toggles, which Svelte handles without much code. If Daniel prefers zero framework, plain TypeScript with a small render function also works; the engine is framework-free either way.

**Reproducibility note.** The "your run vs 1,000 runs" histogram has to come from the same simulator as the live page. The simplest way is to generate it with the TS simulator under Node at build time, so the stream never needs bit-for-bit RNG parity with Python. Parity tests cover the **statistics**, which is what evidence 4 asks for.

## 6. Proposed always-valid method (DECISIONS #3)

**Keep Lyra's method, fix how it is tuned, and add the p-value.**

For the difference in activation rates d̂ with unpooled SE from per-arm counts, and n = total players analysed:

```
half-width(n) = SE · sqrt( 2(nρ²+1)/(nρ²) · ln( sqrt(nρ²+1) / α ) )
```

This is `cs_multiplier` exactly. The same normal-mixture martingale gives the always-valid p-value with no extra machinery:

```
z = d̂ / SE
Λ_n = (nρ²+1)^(-1/2) · exp( nρ² z² / (2(nρ²+1)) )
p_n = min(1, min over looks m ≤ n of 1/Λ_m)
```

Λ_n = 1/α exactly where the band touches zero, so the p-value and the interval always agree. Under a normal mixing distribution this is the same statistic as the mSPRT (Johari et al. 2017): ρ² plays the role of the mixing variance τ². One implementation therefore covers both names, and we don't need a separate mSPRT.

- **Tuning.** Choose ρ² to make the band tightest at the planned maximum sample N, rather than Lyra's fixed 0.05:
  ```
  ρ² = (−2 ln α + ln(−2 ln α + 1)) / N
  ```
  The validity script checks false alarms and coverage at the chosen N.
- **Segments.** Use the same formula at α / K, where K is the number of segment levels shown (Bonferroni). Conservative, simple, easy to explain.
- **Guardrail.** Use the same CS on the difference in means of net revenue, from Σy and Σy² per arm, and gate with `non_inferior`.
- **Not proposed now:** betting confidence sequences. They are tighter for bounded outcomes but need per-player wealth updates, not running totals, and are harder to explain. Possible stretch after M9.

## 7. Questions for Daniel

1. Approve the method in §6 (normal-mixture CS + p-value, ρ² tuned to max sample)?
2. Approve the stack in §5: Svelte 5 + TS + Vite + Vitest, or plain TS without a framework?
3. OK to copy the theory notes listed in §3 into `docs/theory/` (with a source line), so the repo stands alone?
4. Still open, not needed yet: persona model and budget (before M7), hosting (before M6).
