# Log

Newest first. One entry per working session: what was done, how it was checked, what deviated from the brief.

## 2026-10-12 — M10 (part 4): 'Ship it to whom?' on the page (milestone 10 complete, stop for review)

- Daniel approved notebook 08 and the proposed headline (lead with the economics, show the forest and its tests as they are).
- `scripts/targeting_page.py` → `web/public/targeting.json`: rule values by experiment size from `results/08_targeting.json`, and the simulator's truth by tier × channel recomputed on notebook 08's population. Nothing is fitted for the page.
- `TargetingSection.svelte` at the end of the *After* tab (shown whether or not the visitor's run has finished; it is about simulated experiments, not their run): one-sentence answer, size switch (15,000 / 30,000 planned / 14 days), dot-and-range chart of the four rules per 1,000 new players with 'best groups, if known' and 'best possible' marks, why the low-baseline rule works and its assumption, truth grid by tier × channel, 'Why not a causal forest?' with the test rates, and a method toggle (KaTeX).
- Guards: `tests/test_targeting_page.py` (page numbers = cached experiments; truth adds up), and notebook 08's parity cell checks the page's truth against the notebook.
- Python 68 tests, TS 49 tests, svelte-check clean, build OK. Screenshots at 1300 px and 520 px.

## 2026-10-12 — M10 (part 3): notebook 08, targeting (stop for review)

**Built**
- `notebooks/08_targeting` (+ `.py`): who should get the Starter Bonus, on one Small-preset experiment of 30,000 players, split in halves (A fits, B judges), scored against the simulator's truth on a fresh 200,000-player population. Value of a bonus per player is the guardrail's `value_from_lift` applied to each player's lift and baseline, so each player has a personal break-even.
- Methods, all from libraries: econml `CausalForestDML` (honest, R-learner; the CUPAC score as a control only), `DRTester` (calibration test and targeting curve on half B), `SingleTreePolicyInterpreter` (depth-2 tree with per-player costs); doubleml `DoubleMLIRM.gate` (tier × channel subgroup effects with joint intervals) as the baseline; statsmodels joint Wald test of arm × segment interactions as the pre-specified heterogeneity test. Doubly robust scores with the known propensity 1/2.
- A second baseline added after the first results: **average lift, personal baseline** (the CUPAC-adjusted average from half A, the CUPAC score as each player's baseline), plus the check of its assumption (arm × score interaction).
- 75 repeated experiments (25 each at 15,000, 30,000 and the full 14 days, ~100,000), cached per experiment in `results/08_targeting.json`. Figures `08_truth_by_cell`, `08_estimates_vs_truth`, `08_value_by_rule`, `08_policy_tree`.
- Installed the `article` extra (econml 0.17.0, doubleml 0.11.4); no other package changed.

**Results** (true value per player; everyone 0.68¢, best rule by cell 1.45¢, best possible 2.05¢)
- Average lift, personal baseline: 1.36 / 1.58 / 1.68¢ at 15k / 30k / 14 days. Causal forest: 0.98 / 1.09 / 1.32¢. Subgroups: 0.83 / 1.01 / 1.19¢. The forest beats subgroups in 76 / 48 / 60% of runs but never beats the cost-side rule at 30k or more.
- The forest finds little real heterogeneity: calibration slope 0.07–0.13 on average (1 = right), significant in 8 / 8 / 20% of runs; the pre-specified test in 20 / 28 / 64%. Under the brief's safeguard, a typical 30k run would show no segment list.
- The main 30k experiment is an unlucky draw (half A estimates the average lift at +0.5 points vs +2): every fitted rule there is at or below treating everyone. Stated in the notebook.
- **Open for Daniel:** what the page's 'Ship it to whom?' section shows. Proposed headline: targeting is mostly an economics question (skip players likely to activate anyway), with the forest shown as the brief's method and its tests as they are.

**Found and fixed: a hang in the simulator**
- The journey loop redrew only the milestone time until it fell inside the 72 h window. An activated player whose drawn start was already past the window (about 1 in 50 million; seed 20263027) looped forever. This stalled the first notebook run until its one-hour cell timeout. `ablab/simulator.py` now redraws the start in that case; `story.ts` (capped, so it could not hang, but could show level 5 before the first game) does the same. Other seeds are unchanged; fixtures regenerate identically. New test `test_late_start_does_not_hang`. Python 66 tests, TS 49 tests pass.
- The repetitions now save after every experiment and print progress, so an interruption loses nothing.

## 2026-10-12 — M10 (part 2): KaTeX maths on the Before tab; notebook 06 brought in line

- *Before* → 'Show the maths' now renders block formulas with KaTeX (`web/src/lib/components/Tex.svelte`, `katex` 0.16, bundled, no network): break-even (with the plan's +1.71), the one-look sample size (≈16,632 with CUPAC), and the always-valid interval with ρ² tuning (split in two lines for phones). Inline symbols in the prose too.
- **Found:** the first patch wrote the formulas through a non-raw string, so `\f`, `\b`, `\t`, `\r`, `\a` became control characters and KaTeX printed red source. Rewritten from a file; a `\\` line break inside Svelte's `String.raw` was also collapsed, so the ρ² formula is its own block. Screenshots checked at desktop and narrow widths. KaTeX adds a chunk-size warning in the build (fine for now; can be lazy-loaded).
- Notebook 06: the guardrail is now the CUPAC lift interval mapped through G(Δ) = (V − c)Δ − c·p_C with the running control rate (same as production), replacing the separate per-player value interval. Model text explains why and shows G > 0 ⇔ Δ > break-even. Results: guardrail ±2.9¢ per player at 30,000 (was ±3.6¢); brief rule ships +1.0 in 31.5%, strict rule ships +2.0 in 3.3%; CUPAC false verdicts 1.70%, coverage 98.8%, width ratio 0.937. Parity cell extended: `ablab.guardrail.value_from_lift` reproduces the notebook's guardrail.
- svelte-check clean, build OK. Preview server stopped.

## 2026-10-12 — M10 (part 1): Before and After sections; guardrail derived from the lift

- Daniel asked about a stricter 'does it pay' and a stronger CUPAC: both are config changes (no rewrite) but neither makes 'pays' provable at 30,000 players; parked in the backlog.
- `scripts/plan_page.py` → `web/public/plan.json` (break-even +1.71, 83.9% power there, one-look N 16,632 with CUPAC; power curve over 10 lifts, 2,000 runs each).
- Page tabs Before / Live / After (bare #anchors). *Before*: one sentence, power chart with break-even and players needed, assumptions, maths toggle. *After*: readout of the visitor's run (decision, players, end time, lift and range, pays light, split, balance, harmed groups) and money per 1,000 players with the return per $1.
- **Found:** the After table did not add up (net +$1.16 under value −$1.74 and a return of $0.96 per $1) because money rows used the CUPAC lift while net value used a separate interval on value per player. **Fixed by design:** the guardrail value interval is now derived from the CUPAC lift ((V − c)·lift − c·p_C), in Python (`guardrail.value_from_lift`), the browser and `validity/cupac.py`. Validity unchanged (CUPAC 1.70% false verdicts; +1.0 ships 33.1%; guardrail red by the maximum 12.1% vs 9.0% before).
- Tests: Python 65, TS 49 (new: the money rows add up and 'pays' is exactly 'lift above break-even'). Precomputed runs refreshed.

## 2026-10-12 — Milestone 9 complete: phase-2 statistics (stop for review)

**Built**
- Python: `ablab/cupac.py` (design matrix in a fixed column order, train on week 1, θ/μ on week 2), `scripts/train_cupac.py` → `config/cupac.json` (θ 1.017, μ 0.2185, holdout R² 0.124, identical to notebook 06), `ablab/guardrail.py` (value per player, light, final verdict), `ablab/segments.py` (levels and shares from config, widened interval), `ablab.stats.diff_in_means`.
- Validity: `validity/cupac.py` (CUPAC false verdicts 1.70%, coverage 98.3–98.9%; brief rule ships +1.0 in 33.1%) and `validity/segments.py` (familywise coverage 99.0%; tier-1 harm caught 21.9%, false flags 0.05%). Fixtures `m9.json`.
- Browser: `cupac.ts`, `guardrail.ts`, `segments.ts`, `diffInMeans`; `run.ts` keeps per-arm sums of the adjusted outcome and of value, per-level activations, and three always-valid states (adjusted lift = verdict, unadjusted, value) plus eight segment states. Page: 'Pays for itself' light under the verdict; "Don't ship: it works but doesn't pay" state; details with CUPAC / plain always-valid / usual rows, 'Does it pay?', and segment rows with the honest note. Sentences about paying come from the light only.
- Notebooks 05 and 06 end with production-parity cells (both pass).

**Verified**
- Python 64 tests, TS 48 tests, svelte-check clean, ruff clean, build OK (294 kB JS, 67 kB gzipped).
- Precomputed runs with CUPAC: no effect 1.2% false verdicts; small 93.2% ship (was 89.4%), median 75 s (was 80); large 100%, 17.5 s.
- Screenshots: small preset with details; a below-break-even custom run.

**Found and fixed**
- Two pre-written claims contradicted by the data: harm detection 'in most runs' (actually ~21%) and 'the guardrail stops lifts that don't pay' (it barely bites). Both corrected; the second became Daniel's ship-rule decision.
- The page could say 'isn't worth it' (lift range below break-even) while the light said 'not clear yet' (value interval): the sentence now follows the light only.
- Notebook 05's first parity check compared intervals tuned to slightly different shares; replaced by an exact same-input comparison.

## 2026-10-12 — Notebook 06: CUPAC and the guardrail (awaiting Daniel's decision)

- Drafted `notebooks/06_regression_adjustment.ipynb` (seed 20261019). Earlier cohort (two weeks, standard rewards) trains the CUPAC model; θ = 1.017 and μ_X fixed on the holdout week. Experiments draw 30,000 players from a 403k-player pool built with the production simulator (1,000 runs per scenario, looks every 500).
- CUPAC model: logistic regression on pre-sign-up signals removes 12.4% of variance (AUC 0.73), same as gradient boosting (12.5%); sign-up attributes alone 1.7%. Logistic chosen for browser portability.
- CUPAC validity: false verdicts 1.7% (unadjusted 1.9%); coverage 98.8–98.9%. Width ratio 0.937 vs theory 0.936. Small preset ships 95.6% vs 91.6%, median 13,000 vs 14,000 players. Lin OLS (HC2) cross-check: same estimate, SE 0.0045 vs 0.0046.
- Guardrail defined as projected net value per player (V·Y, minus the expected early-payout cost $0.18 per activated bonus player), not 3-day realised revenue (assumption stated in the notebook).
- **Finding (corrected my pre-written text):** with the brief's rule (ship if lift > 0 and guardrail not red), a below-break-even lift (+1.0, −$0.016/player) still ships in 31.5% of runs; the guardrail is ±3.6¢ wide at 30,000 players vs 1–2¢ economics, so it is almost always grey. Strict rule (ship only when value is shown positive): +1.0 ships 0.1%, but Small (+2) only 2.2%; Large 100%. Product decision for Daniel.
- Fixed figures: unrepresentative example run, '−-3%' labels, a title that contradicted the data.

## 2026-10-12 — Notebook 05: health checks and segments (awaiting review)

- Drafted `notebooks/05_checks_and_segments.ipynb` (seed 20261018; 2,000 runs × 58 looks of ~525 players, exact per-cell simulation over 18 tier × device × channel cells built from the production simulator).
- Split check, fair splits flagged when checked every update: always-valid 1.85% vs χ² 32.7% (α 0.05); at the page threshold (0.001): 0.0% vs 1.4%. Broken splits caught by 30,000: 50.5% → 1%, 51% → 26%, 52% → 99.7% (median 11,373 players), 55% → 100% (median 2,070).
- Device bug (56% of iPhone users treated): overall share 52.4%, split check fires at 3,683 players, iPhone/Android SMD ±0.113, all other levels within ±0.04.
- Segments (8 levels, always-valid at α/8, tuned to each segment's share): familywise coverage at every look 99.4% (not widened 90.3%, usual 9.2%).
- **Finding (corrected my pre-written text):** harm detection is underpowered. Tier 1 at −2.4 points (overall +0.92) is flagged in only 21% of runs by 30,000 players; unharmed segments falsely flagged 0.1%. A quick one-sided approximation only reaches ~26%. Page wording must be 'no group shows clear harm yet; this check only catches large harms'. Overall harm protection is the guardrail's job (notebook 06).

## 2026-10-12 — Personas deferred

- Cost estimate (Anthropic list prices via the claude-api skill; ~800 input / ~400 output tokens per call, batch −50%): Haiku 5.5 ≈ $0.00014/call, Sonnet 5.5 ≈ $0.0028, Opus 5.5 ≈ $0.0056. €20 (~$22) covers the whole plan on Haiku (~$1.5; ~$4.5 incl. targeting), ~3,000 per experiment on Sonnet.
- Daniel: skip personas for now. M7–M8 deferred; data-source switch hidden (`SHOW_SOURCE`).

## 2026-10-12 — Milestone 6 complete: design pass (stop for review)

**Built**
- Contrast audit (WCAG AA) of every token pair in both themes. Failing before: faint text 2.97:1 (light) / 4.32:1 (dark), gold strokes 2.26:1 (light), control borders 1.46:1. New tokens `--faint`, `--gold-line` (strokes; `--gold` stays for fills), `--border`. After: 26 pairs checked, 0 failing.
- Themes: system default; footer toggle Light / Dark / System sets `data-theme` on `<html>`; remembered in localStorage inside try/catch.
- Phone (≤ 640 px): header shows the brand only; play, speed and a scenario select sit in a fixed bottom bar with safe-area padding; data source and theme in the footer.
- Chart and histogram measure their container and draw at real width (text stays 11 px on a phone; 3 x-ticks under 420 px).

**Verified**
- Headless screenshots: phone light (500 px), desktop dark (1360 px), full phone page dark. Python 49 and TS 38 tests pass; svelte-check clean.
- Keyboard: all controls are native buttons/select; dialog is a native `<dialog>` (focus handled by the browser); 240 dots are out of the tab order, 'Follow a player' gives keyboard access; visible focus ring in both themes.

**Not done**
- No screen-reader pass and no real-device touch test (headless only).

## 2026-10-12 — M5 review fixes; hosting

- Chart: true-lift label moved into the right margin ('true +2.0'), margin widens only while the line is shown; text next to the peeking ring removed (legend explains it).
- Parallel worlds: 'wrong verdict' is ~0% for both methods whenever the effect is real, so with a real effect the table now shows the lift each method reports when it ships. Measured over 200 worlds: true +2.0 → always-valid +2.47, peeked usual +3.01 (coverage 99.5% vs 66%); true +4.0 → +4.39 vs +4.72. Caption says both overstate (any stop-when-it-looks-good rule does), the peeker most.
- Engine: `verdictD` (estimate at the verdict) and `usualShipD` (estimate when a peeker would first ship).
- Hosting settled: GitHub Pages project site; `.github/workflows/deploy.yml` runs tests, type check and build, then deploys `web/dist`. Goes live once the repo exists (git init still deferred).
- TS: 38 tests passing; svelte-check clean.

## 2026-10-12 — Milestone 5 complete: simulator controls and extras (stop for review)

**Built**
- Engine (`run.ts`): `peek` (first look from the minimum sample where the usual interval excluded zero, with the always-valid range at that moment), coverage of the true lift for both methods, `usualCalls`, `verdictAt`, and `stopAtVerdict: false` (run to the maximum; the first verdict stands).
- `scenario.ts`: presets or custom (true lift −2…+6 points, baseline 10–40%, traffic 100–1,000/h), URL round-trip, `configFor` recalibrates the intercept in the browser (`calibrateIntercept`, bisection on 20,000 reference players).
- `worlds.ts`: 200 parallel worlds, run in batches of 4 so the page stays responsive; tallies wrong verdicts, ships and coverage for both methods.
- `scripts/precompute-runs.ts` (`npm run precompute`, ~2 min) → `public/runs.json`: 1,000 runs per preset with the page engine, stamped with the config's hash. No effect: 1.6% false verdicts (8 ship, 8 don't ship); small: 89.4% ship, median 80 s; large: 100% ship, median 17.5 s.
- Page: 'Adjust' panel (behind a button), 'Reveal the true lift' toggle, peeking marker + legend on the chart, second toggle 'How sure can we be?' with the peeking trap, your run vs 1,000 others (histogram of players to a verdict, no-verdict runs as a count), and 200 parallel worlds.

**Verified**
- TS: 38 tests (new: URL round-trip and broken-link fallback; custom baselines 12% and 30% are what players get; peek is exactly the first qualifying look in 30 runs; run-to-max keeps the first verdict; 120 null worlds: always-valid wrong < 6%, usual > 15%, coverage > 93%; runs.json matches the current config hash; near-zero bounds keep their sign). svelte-check clean.
- Screenshots with everything open (temporary build, reverted). Fixed: histogram dominated by the no-verdict bar; true-lift label colliding with the end label; '0.0 to +4.0 excluded zero' (two decimals near zero).

**Design note**
- Extras sit behind their own toggle so the default screen stays at the four agreed elements; only the peeking marker appears on the chart by default (it is part of the chart's story).

## 2026-10-12 — Milestone 4 complete: player view (stop for review)

**Built**
- Two-column page (players left, analyst right; analyst first below 920 px).
- `Experiences.svelte`: two Questline screens for the fictional Gem Harbor. Identical except the level-5 row: 'Paid when you reach level 10' (locked) vs 'Starter Bonus: paid the moment you get there' (gold). One-line note names the difference.
- `Lanes.svelte`: 'Results coming in'. Lanes show players as they enter the analysis (when their three days are up), not at sign-up, because outcomes are only known then. One dot per 25 analysed players, max 120 per lane, filled = reached level 5 within three days; per-arm counts and rates; drop-in animation (off with reduced motion). Dots are not in the tab order; a 'Follow a player' button opens the newest sampled player for keyboard users.
- `PlayerStory.svelte` + `engine/story.ts`: modal with profile (country tier, device, channel, games installed, click-to-install, partner score), arm, journey (signed up, assigned by hash, started a game, reached level 5 with coins paid now or on hold, or too late / never, counted in the analysis), footnote that only the yes/no outcome feeds the verdict. Journey drawn on demand from the player's ID, same model as `ablab/simulator.py`.
- Backlog: guardrail traffic light (green/grey/red; 'Ship' only if not red) and an economics readout (incremental ROI of the bonus, iROAS-style) per Daniel's question.

**Verified**
- TS: 29 tests (new: stories are reproducible, always agree with the counted outcome — activated ⇒ level 5 before 72 h, late finishers ≥ 72 h —, lanes sample correctly and are capped). svelte-check clean.
- Headless screenshots at 1360 px and 520 px; story dialog checked with a temporary auto-open build (reverted).

**Deviation**
- The brief's 'players arriving' lanes show players entering the analysis rather than signing up: with a 72-hour outcome delay, a dot at sign-up could not yet be filled or empty.

## 2026-10-12 — M3 review fixes

- Daniel's review: timing good; small preset sometimes ends inconclusive (expected: ~89–90% power unadjusted).
- Story rewritten to state the intervention literally: coins are cashable (100 = $1); everyone's first goal is level 5 for 40 coins; standard holds the coins until level 10; Starter Bonus pays them at level 5. Same reward, paid sooner. Metric phrased as 'reach level 5 within three days'.
- Fixed: '−0.0' (points() now rounds before choosing the sign).
- Fixed an overclaim: the inconclusive sentence always said a break-even lift 'would very likely have shown up'. Now it follows the data: if the whole range is below break-even, 'isn't worth it'; otherwise 'this test can't settle it'.
- Fixed: between 1,000 and 2,000 players the band was clipped out of view; the y-axis now fits the latest band until 2× the minimum, and the first banded update is drawn as a thin bar.
- Tests: `format.test.ts` (3 tests). TS suite 26 passing; svelte-check clean.

## 2026-10-12 — Milestone 3 complete: simulator stream and analyst view (stop for review)

**Built**
- Always-valid split check: `ablab.checks.srm_log_bayes_factor` / `srm_always_valid_p` (Dirichlet-multinomial Bayes factor, Lindon & Malek 2022). Matches savvi 0.3.1 to 1e-9 on 6 hard-coded reference values plus a batched update (savvi run in a separate env; it needs cvxpy). Added to fixtures and ported to TS.
- `web/src/lib/engine/`: `rng.ts` (pure-rand xoroshiro128+, 53-bit uniforms, Marsaglia normal, PTRS Poisson as numpy), `simulator.ts` (player-level port of the world, hour by hour), `run.ts` (clock, sign-ups, 72 h maturity, running totals per arm and covariate level, always-valid state, split check, verdict, max-sample cap), `checks.ts`.
- Page (`web/src/App.svelte`, `LiftChart.svelte`, `Details.svelte`, `format.ts`): verdict with icon, live sentence, clock + 'n of 30,000 planned' + range line; SVG chart (fixed x to 30,000, band = intersected confidence sequence, estimate from 500 players, minimum-sample marker); details (always-valid vs usual rows, split check, balance table); play/pause, 1×/5×/skip to end, scenario buttons, run again; seed, preset and details in the URL; light/dark via system setting.

**Verified**
- TS: 23 tests (parity + stream): Poisson/normal moments; checks match Python; world calibrated (baseline 22%, lift = preset, 50/50); runs replay exactly from a seed; no verdict before 1,000 players; **300 no-effect browser runs: false verdicts under 5%**; default preset median **85 s** (asserted 60–90 s).
- Python: 49 tests; validity re-run at 525 players per update: false verdicts 1.45%, coverage 98.6–98.9%.
- `svelte-check` clean; `vite build` OK (253 kB JS, 53 kB gzipped). Headless Chrome screenshots at 1280 px and 500 px: run plays to 'Ship' at 22,674 players for seed 4242; details render; no horizontal overflow at 500 px.

**Deviations / found**
- Timing re-tuned (start hour 80, 1.75 h per update): see DECISIONS. Cause documented: no CUPAC yet and a night-time start.
- y-axis fitted from 2× the minimum sample; the first, widest stretch of the band is clipped at the plot edge.
- Not yet: player half (M4), section tabs (shown when Before/After exist, M10), theme toggle and phone polish (M6), personas (disabled button).

## 2026-10-12 — Milestone 2 complete: browser port (stop for review)

- Renamed 'refresh' to 'update' in config and validity output (`hours_per_update`, `seconds_per_update`): the page updates itself every 2–3 s; nothing is reloaded. Validity re-run, unchanged results.
- `web/`: Svelte 5.57 + TypeScript 5.7 + Vite 6.4 + Vitest 3.2, `smol-toml` to read `config/simulator.toml`, stdlib `erfc` for normal tail probabilities.
- `web/src/lib/engine/`: `assign.ts` (MurmurHash3 x86_32 on UTF-8 bytes), `stats.ts`, `sequential.ts` (incl. `AlwaysValidState`, the per-update running intersection and running-min p-value the page keeps), `config.ts`.
- `parity.test.ts` (validity evidence 4): 9 tests, all pass. Hash bit-exact on 204 ids incl. empty and non-ASCII; usual interval, always-valid interval, per-look and always-valid p-values, intersected interval and verdict match Python at every look of 4 paths, relative tolerance 1e-9; all four verdicts covered; config read identically.
- Mutation check: changing ρ² by 1e-7 relative makes the suite fail. `tsc --noEmit` clean.
- Deviation: the seeded PRNG for the live stream moves to M3, since parity is required for the statistics, not for the browser's simulated players.
- Heads-up: `web/node_modules` sits inside OneDrive and will sync thousands of files.

## 2026-10-12 — Milestone 1 complete: Python reference engine (stop for review)

**Built**
- `config/simulator.toml`: every parameter (world, calibration, plan, page). Page decisions: join at hour 72, 1.5 h per refresh, default preset Small real effect, min 1,000 / max 30,000 players, N* = 30,000.
- `ablab/`: `config`, `assign` (mmh3), `simulator` (player-level, identical to notebook 01; plus fast aggregate `simulate_counts`), `stats` (usual interval), `sequential` (confidence sequence, always-valid p-value, running intersection from the minimum sample, verdict rule), `power`, `checks` (SRM χ², SMD).
- `tests/`: 41 tests. Each module checked against an established library: mmh3 test vector, statsmodels Wald interval and p-value, gbstats sequential test (interval and p-value to 1e-9), statsmodels power, scipy χ², causalml SMD. Plus property tests: p-value never rises, p < α exactly when an interval excluded zero, intersection only narrows and skips looks before the minimum.
- `validity/always_valid.py` → `results/always_valid.json` (2,000 runs, seed 20261016), checked every page refresh (450 players) and every 50 players: false verdicts 1.25% / 1.40% (usual interval 30.1% / 37.8%); coverage at every look 97.9–99.2% across presets (usual 60.6–70.5%). All PASS.
- `scripts/make_fixtures.py` → `fixtures/{assign,stats,sequential}.json` for the TypeScript port; sequential paths cover all four verdicts.
- Each notebook ends with a *Production parity* cell; all four pass (notebook 01: 100,723 identical players).

**Deviations from the brief / plan**
- Notebooks keep their own readable code plus a parity cell, instead of switching to `import ablab` (better as blog material; drift still caught).
- Running intersection starts at the 1,000-player minimum (an early, misleadingly narrow interval must not be carried forward).
- Validity runs on the unadjusted estimate; CUPAC-adjusted validity is shown in notebook 06 (M9), where the adjustment is built.
- Fixed a pytest trap: statsmodels' `test_proportions_2indep` was being collected as a test (same issue existed in Vega).

## 2026-10-12 — Notebook 04: power and planning

- Drafted `notebooks/04_power_and_planning.ipynb` (seed 20261015). Fictional economics in `PLAN`: bonus $0.40, 55% of activated players reach level 10, $2.50 lifetime net margin per activation, 300 sign-ups/hour.
- Break-even lift **+1.71 points** (the smallest effect worth detecting).
- Fixed horizon at 80% power (statsmodels `NormalIndPower` and closed form agree within 2 players): 18,991 unadjusted, 16,598 with CUPAC.
- Sequential (always-valid, simulated; Gaussian increments with common random numbers; reproduces notebook 03's 73% power check at 73.1%): N_max for 80% power at break-even = 35,000 unadjusted, **30,000 with CUPAC** (14% fewer). About 1.8× the one-look N, but at break-even the median stop is 14,750 players, earlier than the one-look 16,598.
- 30,000 players = 4.2 days of sign-ups + 3 days for outcomes.
- **Brief conflict found:** 'one refresh = one experiment hour' cannot meet 60–90 s because of the 72 h outcome delay. Two options computed (A: join at launch, ~4 h/refresh → small preset 73 s; B: join at hour 72, ~1.5–2 h/refresh → small preset 55–110 s). Open decision for Daniel.
- 5 figures in `figures/04_*`, reviewed and fixed.

## 2026-10-12 — Realistic pre-sign-up signals added to the simulator

- Daniel: build the realistic dataset from the start; the page shows the final (CUPAC-adjusted) analysis; notebooks keep their order.
- Notebook 01 now has latent engagement U ~ N(0,1) (β_U = 1.2) and three pre-sign-up signals: games installed in the last 30 days (Poisson), click-to-install seconds (log-normal), partner score (paid social only). Strengths tuned in a scratch script to land in DoorDash's reported 10–20% CUPAC range.
- New section "How predictable is activation before sign-up?" (gradient boosting, trained on week 1, scored on week 2): sign-up attributes 1.5%, + signals 12.6%, oracle 19.7% of variance. Two new figures.
- Logit recovery now includes U: β_U recovered as 1.196 (true 1.20); 6 of 7 intervals cover the truth. The text now says so honestly (one miss in seven is expected ~30% of the time).
- Added scikit-learn to the notebooks extra.

## 2026-10-12 — Variance reduction note

- New theory note `docs/theory/variance-reduction.md`: CUPED, Lin adjustment, CUPAC (DoorDash blog, 2020; not a paper), MLRATE (Guo et al., NeurIPS 2021), combining with confidence sequences (Waudby-Smith et al.; Lindon et al.), and the new-player problem. Sources verified by web search.
- Quick calculation from the notebook 01 model: sign-up attributes explain at most 2.4% of activation variance (interval × 0.988). Daniel chose to show both the honest small gain and a CUPAC payoff with one added pre-sign-up signal (notebook 06).

## 2026-10-12 — Notebook 03: the always-valid interval

- Daniel approved the *Before the experiment* section (power and planning); recorded in DECISIONS.md, backlog updated, notebook 04 renamed `04_power_and_planning`.
- Drafted `notebooks/03_always_valid.ipynb` (seed 20261014, N* = 20,000 placeholder, α = 0.05): normal-mixture confidence sequence, always-valid p-value (running min of 1/Λ), ρ² tuned to N*. About 10 lines of our own code.
- Checked against `gbstats.SequentialTwoSidedTTest` at 8 random looks: interval and per-look p-value equal to rtol 1e-9.
- Validity (2,000 experiments × 400 looks per preset, counted from 1,000 players):
  - Evidence 1: false verdicts under no effect **1.60%** (Wilson 95% CI 1.14–2.25%). PASS. Same 1.60% counted from the first look.
  - Evidence 2: coverage at every look 98.40% / 98.05% / 98.20% (no / small / large effect). PASS.
  - Evidence 3: usual interval, same checking: 34.1% false verdicts from 1,000 players (47.8% from the first look); coverage about 64–66%.
- Early power read: Large effect ships by 20,000 in 100% of runs (median 3,334 players); Small effect in 73% (median 10,552).
- Found that a plain confidence sequence can clear zero and later drift back. **Decision proposed and implemented in the notebook:** the page shows the running intersection, which only narrows; coverage is identical (shown).
- 8 figures in `figures/03_*`, reviewed and fixed (label collisions, two similar golds, 1.4× → 1.55× wording).

## 2026-10-12 — Notebook 02: the peeking problem

- Drafted `notebooks/02_peeking_problem.ipynb`: 2,000 A/A experiments × 400 looks (about 50 players per look, 20,000 per experiment), seed 20261013. Runs in about 11 s.
- Vectorised z-test checked against `statsmodels.test_proportions_2indep` (Wald) at 8 random (experiment, look) pairs: equal to 1e-10.
- Results, with Wilson 95% CIs from `statsmodels`: look once at the end 5.8% (4.8–6.9%); look after every batch **50.4%** (48.3–52.6%). False alarms rise with looks (2 → 9.7%, 10 → 20.3%, 100 → 40.0%) and barely change with experiment size (heatmap). Median first false alarm at 800 players.
- 6 figures in `figures/02_*`, reviewed; z-paths redrawn so red paths stop where a peeker would ship.
- New backlog items: minimum sample before showing a verdict; promote notebook 01 code.

## 2026-10-12 — causalml balance table; gbstats found

- Balance table switched to `causalml.match.create_table_one` (Daniel's pick); categories become 0/1 indicators, so SMD is per level (all |SMD| ≤ 0.012). `tableone` removed.
- **Correction:** the library review wrongly said no installable library implements our always-valid interval. GrowthBook's open-source `gbstats` (`SequentialTwoSidedTTest`) does, with the same ρ tuning; it matches our formula to every printed digit on the notebook 01 run. Adopted as the reference implementation. It pins pandas<2, so it is installed with `--no-deps` plus `pydantic`; verified working on pandas 3.
- OneDrive intermittently locks files in `.venv` during installs ("Access is denied"); retrying works.

## 2026-10-12 — Library review; notebook 01 moved onto standard libraries

- Daniel asked for established libraries instead of hand-written helpers. Installed and tried 12 candidates in a scratch env on our own counts; verdicts in [docs/library-review.md](docs/library-review.md).
- Adopted: `mmh3` (core), `statsmodels`, `seaborn`, `tableone` (notebooks), `doubleml` + `econml` (article). savvi kept as a reference for always-valid SRM and regression adjustment. confseq fails to build on Windows / Py 3.11. spotify-confidence is group-sequential, not always-valid.
- Our always-valid interval stays hand-written (no installable library fits); GrowthBook (Waudby-Smith asymptotic CS, tuned N*) and Statsig (normal mSPRT) implement the same family themselves.
- Notebook 01: hand-written MurmurHash3, balance table, heatmap annotation and histogram overlays replaced by `mmh3`, `tableone`, `seaborn`; added χ² SRM (p = 0.38) and a `statsmodels` logit recovery check (all 6 config coefficients inside their 95% CIs, new figure `01_logit_recovery`). Re-ran top to bottom; figures re-reviewed.
- SRM simulation (300 null runs, 100 hourly checks): hourly χ² falsely flagged 38.7% of runs, savvi 2.3%; savvi caught a real 52/48 split at hour 26. Recorded in docs/library-review.md.

## 2026-10-12 — Notebook 01: players and the data-generating process

- Created `.venv` with uv (Python 3.11; notebooks + dev extras, plus ipywidgets and mmh3). Registered Jupyter kernel "Python (ablab)". Added `.gitignore`.
- Drafted `notebooks/01_players_and_dgp.ipynb` (paired `.py`): case study and experiment description, LaTeX model (Poisson arrivals with daily/weekly rhythm, covariates, logistic baseline, segment-varying additive lift, hash assignment), config block, hand-written MurmurHash3, calibration, simulator, descriptives, 8 figures in `figures/`, slider cell.
- Verified by running top to bottom (about 20 s): MurmurHash3 matches `mmh3` on 2,005 keys; calibrated baseline 22%; true average lift +2.00 points under the Small preset; 49.86% assigned to treatment; all standardised differences below 0.013. One run observed +1.69 points.
- Reviewed every figure as an image and fixed: overnight dip in arrivals, equal bar heights, dumbbell layout for lift by segment, outline-vs-fill journey histograms with readable ticks, hidden first hours of the cumulative preview.
- Choices to review: segment multipliers (tier 3 ×1.5, paid social ×1.25), additive lift on the probability scale, 300 sign-ups/hour placeholder.

## 2026-10-12 — M0 approved, notebook workflow

- Daniel approved the reuse report: method (normal-mixture CS, tuned ρ², matching p-value) and stack (Svelte 5 + TS + Vite, Vitest, Python + uv). Recorded in DECISIONS.md.
- Copied 11 theory notes from Vega into `docs/theory/`, each with a source line. `sequential-chapter.md` is flagged with its two known errors.
- Set up the notebook-first workflow: `notebooks/README.md` (life of a notebook, sections, planned notebooks 01–08), `notebooks/_template.ipynb`, `ablab/viz.py` + `ablab/ablab.mplstyle` (figure colours match the page). Checked: style loads.
- Added `pyproject.toml` (package `ablab`, extras: notebooks, article, personas, dev). Nothing installed yet.
- git init deferred by Daniel.

## 2026-10-11 — Milestone 0 kickoff

- Set up the project skeleton: README, LOG, BACKLOG, DECISIONS, CLAUDE.md, `docs/`, `design/`.
- Moved `live-ab-lab-proposal.md` to [docs/brief.md](docs/brief.md) (content unchanged).
- Surveyed Vega and Vega/lyra read-only; reuse report in [docs/vega-reuse.md](docs/vega-reuse.md).
- Wrote design direction ([docs/design.md](docs/design.md)) and an interactive mockup, [design/mockups/live-lab.html](design/mockups/live-lab.html) (published privately: https://claude.ai/artifact/Ex6aMZvejwdP6n2KyAshjq). Checked: script parses; not yet reviewed on a real phone.
- Spot-checked the surveys against source: `lyra/sequential.py` (CS multiplier, `n or day` fallback), `tests/test_sequential.py::accrue`, and `chassis/scorecard.py` re-sampling each day.
- **Deviation:** mockups were made in milestone 0 at Daniel's request (brief puts design in M6). They are static HTML with placeholder numbers, clearly labelled, and not part of the product.
- **Waiting on:** Daniel's approval of the reuse report and stack before M1.
