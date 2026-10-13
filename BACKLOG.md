# Backlog

Milestones from brief §12. Stop for review after each. `[x]` done, `[~]` in progress, `[ ]` not started.

## M0 — Reuse report, stack, design direction  `[x]`
- [x] Project skeleton (README, LOG, BACKLOG, DECISIONS, CLAUDE.md)
- [x] Survey Vega (read-only)
- [x] Survey Vega/lyra (read-only)
- [x] `docs/vega-reuse.md`: reuse as-is / adapt / leave behind / stacks / proposed stack
- [x] `docs/design.md` + first static mockups
- [x] **Daniel approves reuse report and stack** (2026-10-12)
- [x] Copy theory notes to `docs/theory/`
- [x] Notebook workflow: template, plot style (`ablab/viz.py`), conventions

## M1 — Python reference engine and tests  `[x]` (awaiting review)
Built notebook-first (see `notebooks/README.md`): notebooks 01–04, reviewed, then promoted.
- [x] `01_players_and_dgp` notebook (reviewed 2026-10-12; switched to standard libraries)
- [x] `02_peeking_problem` notebook (reviewed 2026-10-12)
- [x] `03_always_valid` notebook (reviewed 2026-10-12)
- [x] `04_power_and_planning` notebook: break-even MDE, fixed-horizon N (statsmodels power), sequential max sample and expected stopping time (simulation), tick/batch tuning
- [x] Running-totals analysis (`ablab/stats.py`, `ablab/sequential.py`); per-segment totals in M9
- [x] Naive diff-in-proportions: CI and p-value (= statsmodels Wald)
- [x] Always-valid confidence sequence and p-value (= gbstats), running intersection from the minimum sample
- [x] SRM χ² and SMD from counts (always-valid SRM in notebook 05)
- [x] Hash assignment (mmh3)
- [x] Simulator in `config/simulator.toml` + `ablab/simulator.py` (incl. pre-sign-up signals)
- [x] Re-run validity evidence 1–3 at N* = 30,000 (the planned maximum)
- [x] Validity script: null FPR ≤ 5% over ≥ 2,000 runs with peeking every refresh; coverage ≥ 95% per preset; naive FPR reported
- [x] Tune refresh/batch/max-sample so the default preset reaches a verdict in 60–90 s
- [x] Minimum sample before any verdict is shown: 1,000 players
- [x] Promote notebooks 01–04 into `ablab` with tests and parity cells
- [x] Fixtures for the browser port (`scripts/make_fixtures.py`)

## M2 — Browser port  `[x]` (awaiting review)
- [x] Port engine to TypeScript (`web/src/lib/engine/`: assign, stats, sequential incl. running state, config)
- [x] Parity tests against `fixtures/` at relative tolerance 1e-9 (hash bit-exact); mutation check confirms they bite
- [x] Same hash in both languages
- [ ] Seeded PRNG for the live stream (moves to M3: the stream is simulated in the browser; parity is on the statistics)

## M3 — Simulator stream and analyst view  `[x]` (awaiting review)
- [x] Update loop (2–3 s with jitter, hourly Poisson sign-ups, 72 h outcome delay), seed and preset in URL
- [x] Verdict + live sentence + range line, lift-over-time chart with zero line and narrowing band
- [x] Details toggle: always-valid vs usual interval, always-valid split check, balance table (segments → M9)
- [x] Play / pause / speed (1×, 5×, skip to end), run again
- [x] Seeded PRNG (pure-rand xoroshiro128+, PTRS Poisson), browser-stream tests
- [x] Phone: controls take three rows above the verdict; chart ticks small (fixed in M6)

## M4 — Player view  `[x]` (awaiting review)
- [x] Two experiences: Questline screens for Gem Harbor; only the level-5 row differs (held until level 10 vs paid straight away)
- [x] Lanes: 'Results coming in', one dot per 25 analysed players (filled = reached level 5 in three days), per-arm counts and rates
- [x] Player story on tap (and 'Follow a player' for keyboard users): profile incl. pre-sign-up signals, arm, dated journey, honest footnote
- [x] Default screen: two experiences, lanes, verdict, chart (plus header and story)

## M5 — Simulator controls and extras  `[x]` (awaiting review)
- [x] Presets plus 'Adjust': three sliders (true lift, baseline with in-browser recalibration, traffic); custom scenarios in the URL
- [x] Reveal the true lift (line on the chart); 200 parallel worlds (in the browser, batched, with progress)
- [x] Peeking counter (marker on the chart + explanation); your run vs 1,000 pre-computed runs (`npm run precompute`, config-hash checked)

## M6 — Design pass  `[x]` (awaiting review)
- [x] Reviewed against brief §9 at 1360 px and 500 px, light and dark (headless screenshots)
- [x] Contrast: 26 colour pairs ≥ WCAG AA (text 4.5:1, graphics 3:1); keyboard: native buttons/dialog, visible focus, dots out of tab order with 'Follow a player'; reduced motion respected; play/pause for the auto-updating content
- [x] Hosting decided (GitHub Pages)
- [x] Phone: controls in a bottom bar; chart and histogram drawn at real width; theme toggle (light / dark / system)
- [ ] Not done: screen-reader pass on a real device; touch test on a real phone

## M7 — Persona pilot  `[deferred]` (Daniel, 2026-10-12)
- [ ] Decide model and budget (DECISIONS #5)
- [ ] Generation script: env API key, hard call cap, structured output
- [ ] 200-call pilot report: outcome rate per arm, response variance

## M8 — Persona source  `[deferred]`
- [ ] Full runs: Starter Bonus (~5,000) + A/A
- [ ] Replay with rich player stories; "recorded run, replayed" label

## M9 — Phase 2 statistics  `[x]` (awaiting review)
- [x] `05_checks_and_segments` notebook: always-valid split check, balance under a randomiser bug, segment monitoring (harm check honest but underpowered)
- [x] `06_regression_adjustment` notebook: CUPAC (logistic on pre-sign-up signals, θ fixed from an earlier cohort), guardrail as projected value per player, 'it works' vs 'it pays'
- [x] Python: `ablab/cupac.py`, `scripts/train_cupac.py` → `config/cupac.json`, `ablab/guardrail.py`, `ablab/segments.py`, `diff_in_means`; 64 tests; `validity/cupac.py`, `validity/segments.py`; fixtures `m9.json`
- [x] Browser: verdict on the CUPAC-adjusted always-valid interval; 'Pays for itself' light; 'Don't ship: doesn't pay' state; details with three interval rows, 'Does it pay?', segment rows; parity tests; precomputed runs refreshed (hash covers cupac.json)
- [ ] Not built: one-sided harm boundary (would need a proper one-sided mixture; small gain)

## M10 — Before and after the experiment  `[x]` (awaiting review)
- [x] *Before the experiment* section: one sentence, power chart with break-even and players needed, assumptions, maths toggle (`scripts/plan_page.py` → `web/public/plan.json`)
- [x] Live verdict line shows 'n of N planned players'
- [x] End-of-run readout (*After* tab), incl. economics per 1,000 players: extra activations, revenue, bonus cost, net value, incremental ROI of the bonus (iROAS-style) and payback
- [x] `08_targeting` notebook: causal forest (econml), honest split, heterogeneity tests, DoubleML subgroup baseline, cost-side baseline, 75 repeated experiments (reviewed 2026-10-12)
- [x] 'Ship it to whom?' page section from notebook 08 (`scripts/targeting_page.py` → `targeting.json` → `TargetingSection.svelte`)

## Open
- [ ] Website name: something fun (repo is "Always-Valid A/B Testing"; page still says "Live A/B Lab"). Daniel to decide.

## Ideas parking lot (not in scope unless Daniel says so)
- Stricter 'does it pay': only via config (≈20× more players, kinder economics, or bigger presets); notebook 06 shows the +2 preset pays only ~0.7¢/player vs ±2.9¢ precision
- Stronger CUPAC: stronger or extra pre-sign-up signals (config + retrain); 30% R² would narrow intervals ~16%, still far from proving 'pays'
- Sound on verdict change
- Shareable result card image
