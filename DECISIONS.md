# Decisions

From brief §11. Update the status column when Daniel decides; add the date.

| # | Decision | Default | Status |
|---|---|---|---|
| 1 | Product and company names | Keep "Live A/B Lab", "Questline", "Starter Bonus" | Default |
| 2 | Technology stack | Proposed in [docs/vega-reuse.md](docs/vega-reuse.md); must build to a static site | **Settled** 2026-10-12 |
| 3 | Always-valid method and tuning | Reuse Vega/Lyra if tested; else proposed in reuse report | **Settled** 2026-10-12 |
| 4 | Refresh length, batch size, max sample | Tune by simulation to a 60–90 s verdict | **Settled** 2026-10-12: max sample 30,000 (= N*); visitor joins at hour 72; 1.5 experiment hours per refresh; minimum 1,000 players before any verdict |
| 5 | Persona model and budget | No default | **Deferred** 2026-10-12: personas skipped for now (estimate kept in LOG) |
| 6 | Segments in the live table | Country tier, device, acquisition channel | Default |
| 7 | Hosting | No default | **Settled** 2026-10-12: GitHub Pages project site, dannyredel.github.io/live-ab-lab |
| 8 | Build the targeting article | Yes, last | Default |

## Settled

| Date | Decision | Why |
|---|---|---|
| 2026-10-11 | Brief lives at `docs/brief.md` | Keep the root for project files |
| 2026-10-12 | Always-valid method: normal-mixture confidence sequence (Lyra's), ρ² tuned to the max sample, plus the matching always-valid p-value | Approved from reuse report §6. Same statistic as a normal-mixture mSPRT. |
| 2026-10-12 | Stack: Python 3.11 + uv (numpy, scipy) reference engine; Svelte 5 + TypeScript + Vite page; Vitest parity tests; hand-drawn SVG charts | Approved from reuse report §5 |
| 2026-10-12 | Theory notes copied from Vega into `docs/theory/` with source lines | Daniel plans technical blog articles from them |
| 2026-10-12 | Notebook-first: every model is built and reviewed in a notebook (LaTeX model, libraries, data, descriptives, figures, results) before promotion to `ablab/` with tests | Daniel's working style; see `notebooks/README.md` |
| 2026-10-12 | git init deferred | Daniel's call |
| 2026-10-12 | Notebooks and the Python reference use established libraries (statsmodels, scipy, mmh3, seaborn, tableone; econml/doubleml later). The browser engine stays a hand port, tested against library results | Daniel: notebooks should read like DS/research work. See docs/library-review.md |
| 2026-10-12 | Heterogeneous lift as designed (tier 3 ×1.5, paid social ×1.25) | Daniel agreed |
| 2026-10-12 | **Scope added:** a *Before the experiment* section (power and planning). Section bar becomes Before → Live → After. One sentence, one chart (chance of 'ship' and players needed, by true lift, with break-even marked), maths behind a toggle; live verdict line shows 'n of N planned players'. Built near the end with *After the experiment* | Daniel approved. Power analysis already sets the max sample and the CS tuning N*; this makes it visible |
| 2026-10-12 | Smallest lift worth detecting comes from break-even economics (bonus cost per player ÷ value per activation), with fictional numbers in the config | Ties the test size to the business decision; same numbers feed the guardrail and targeting article |
| 2026-10-12 | The page draws the running intersection of the confidence sequence, so the interval only narrows and a verdict never flips back | Same coverage guarantee (shown in notebook 03); matches the brief's 'interval narrowing' |
| 2026-10-12 | Notebook 06 does both: regression adjustment on sign-up attributes (honest, tiny gain: best R² 2.4%), then one realistic pre-sign-up signal (e.g. partner engagement score on paid installs) + a CUPAC model trained on an earlier cohort | Daniel chose option 3. See docs/theory/variance-reduction.md |
| 2026-10-12 | The simulated world includes realistic pre-sign-up signals from the start (latent engagement U; games installed in last 30 days, click-to-install time, partner score on paid social). The page showcases the **final analysis**: verdict from the CUPAC-adjusted always-valid interval; details also show the unadjusted always-valid and the usual interval. Notebook order stays as a teaching progression | Daniel. CUPAC model trained on week 1 explains 12.6% of week-2 variance (realistic vs DoorDash's 10–20%) |
| 2026-10-12 | Page starts at hour 72 (first outcomes arriving), 1.5 experiment hours per refresh; default preset 'Small real effect' (+2 points) | Daniel agreed. Notebook 04: median verdict about 73 s for the default preset |
| 2026-10-12 | Page timing re-tuned in the browser stream: visitor joins at **hour 80** (day 4, 08:00) with **1.75 h per update**. Median verdict for the default preset 85 s (120 runs) | Notebook 04's 73 s assumed CUPAC and steady arrivals; the browser stream has neither yet (unadjusted until M9; night-time cohorts mature first at hour 72). Joining at 08:00 also shows ~300 players on the first update instead of 44 |
| 2026-10-12 | The page's split check is the always-valid SRM test (Lindon & Malek; savvi), flagged at p < 0.001, not χ² | A χ² checked at every update falsely flagged 38.7% of fair runs |
| 2026-10-12 | Hosting: GitHub Pages project site (repo `live-ab-lab` → dannyredel.github.io/live-ab-lab), deployed by `.github/workflows/deploy.yml` after tests pass | Daniel delegated. Lives next to his existing dannyredel.github.io; static site needs nothing Vercel adds (per-PR previews, server functions) |
| 2026-10-12 | Parallel worlds: with no effect, show wrong verdicts; with a real effect, show the lift each method reports when it ships (winner's curse) | Daniel noticed 'wrong verdict' is always 0% with a real effect. 200 worlds at +2: always-valid reports +2.47, peeking at the usual interval +3.01 |
| 2026-10-12 | Phone layout: playback and scenario in a fixed bottom bar; data source and theme in the footer | Verdict sits under the intro instead of below three rows of controls |
| 2026-10-12 | Theme: system by default, light/dark toggle in the footer, choice kept in localStorage (convenience only) | Brief §9 light and dark themes |
| 2026-10-12 | Synthetic personas (M7–M8) deferred; the data-source switch is hidden until they exist | Daniel. Estimate on record: with a €20 cap, Haiku 5.5 covers the full plan (~$1.5–4.5, batch); Sonnet 5.5 only ~3,000 per experiment. Pilot would cost < $2 |
| 2026-10-12 | 'Ship' means 'it works' (lift interval above zero, guardrail not red); a 'Pays for itself: yes / not clear yet / no' light sits under the verdict; a confirmed lift with a red guardrail becomes "Don't ship: it works but doesn't pay" | Daniel chose this after notebook 06: at 30,000 players the value per player is only known to about ±4¢, so a strict 'it pays' rule would almost never ship the +2 preset |
| 2026-10-12 | Guardrail = projected net value per player (V·Y, minus the expected early-payout cost $0.18 per activated bonus player), not 3-day realised revenue | 3-day revenue would penalise paying earlier while most value arrives later; same economics as the break-even |
| 2026-10-12 | Everything the verdict sentence says about paying comes from the guardrail light alone | Avoids two different answers to 'does it pay?' on one screen (found in screenshots) |
| 2026-10-12 | Segment rows say 'no group shows clear harm yet; this check only catches large harms' | Notebook 05: a −2.4-point harm in tier 1 is caught in ~21% of runs by 30,000 players |
| 2026-10-12 | Guardrail value interval is derived from the CUPAC lift interval: value = (V − c)·lift − c·p_C (p_C plug-in), instead of a separate interval on value per player | One source for every 'pays' statement: light, sentences, money table and return per $1 now always agree (a screenshot showed +$1.16 net next to $0.96 per $1). Sharper too; notebook 06's conclusion unchanged (+1.0 still ships 33%) |
| 2026-10-12 | Page sections: Before / Live / After as tabs with bare #anchors; the live run keeps going while another tab is open | Brief §3.3 section bar; DECISIONS 'Before the experiment' scope |
