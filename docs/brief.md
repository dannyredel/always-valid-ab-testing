# Live A/B Lab — Build brief (v1.0)

Last updated: October 2026
Owner: Daniel Redel
Status: ready for implementation. Names ("Live A/B Lab", "Questline", "Starter Bonus") are working names.

---

## 0. Instructions for Claude Code — read this first

1. **Read this whole file before doing anything.**
2. **Then read the existing project at `C:\Users\danny\OneDrive\Projects\Vega`, including the Lyra project inside it at `C:\Users\danny\OneDrive\Projects\Vega\lyra`.** Both contain theory notes and code that can be recycled here (statistics engine, tests, write-ups). Read the `lyra` subfolder explicitly; do not assume a pass over the top level of Vega covers it.
   - Treat both as read-only. Do not edit, move or delete anything in them.
   - If either folder is not accessible from the current workspace, stop and ask Daniel to grant access. Do not skip this step or guess at the contents.
3. **Write a short reuse report** to `docs/vega-reuse.md` in this project, covering Vega and Lyra separately:
   - what can be reused as-is (modules, tests, derivations), with paths;
   - what needs adapting, and why;
   - what should not be carried over;
   - the stack each of them uses, and the stack you propose for this project.
4. **Stop and wait for Daniel's go-ahead** after the reuse report. Do not start building before that.
5. **This is a new, separate project.** Copy what is reused into this repository; do not import from or depend on the Vega folder. Reuse logic and theory, not the interface: this project must not look or navigate like Vega or Lyra. It should be simpler, calmer and visually more appealing (section 9).
6. **Work in milestones** (section 12). Stop for review at the end of each one, with a short note on what was built, how it was verified, and anything that deviated from this brief.
7. **Do not invent results.** Every number shown on the page comes from the engine. Every claim about validity is backed by a test or simulation in the repository.
8. **Ask before deciding** anything in section 11 that has no default, and before adding scope that is not in this brief.

---

## 1. The idea in one paragraph

A single web page where a visitor watches an online experiment run live: players arrive every few seconds, the estimated effect and its interval update on screen, and the page says when the result is safe to act on ("ship", "don't ship", or "keep collecting"). It does not depend on real visitor traffic. Data comes from two sources that feed the same screen and the same statistics engine: a known-truth simulator, and a recorded experiment on synthetic personas.

What it should prove: that Daniel can design an online experiment, analyse it with methods that stay valid under continuous monitoring, and ship it as a working product that a non-specialist can read.

Scope rule: the page shows what an experimentation platform monitors live and continuously. Anything that cannot update on every refresh is a companion piece, not part of the live page.

## 2. The case study

Stated at the top of the page, in plain language:

> **Questline** is a (fictional) rewarded-gaming marketplace. Players discover mobile games on Questline and earn coins for reaching milestones in them. Game studios pay Questline for every milestone a player reaches, and Questline passes part of that on as the reward.
>
> Many new players sign up and never finish a first game. The product team wants to test a **Starter Bonus**: the first, easy milestone pays out straight away instead of only at a later level.
>
> For two weeks, new players are randomly split. Half see the standard reward schedule (control), half get the Starter Bonus (treatment). **Does the Starter Bonus get more new players to complete their first milestone, and is it worth what it costs?**

| Element | Choice |
|---|---|
| Unit | New player, assigned once at sign-up |
| Split | 50 / 50, by hash of player ID |
| Primary metric | Activation: completes a first paid milestone within 72 hours (yes / no) |
| Guardrail (phase 2) | Net revenue per player (studio payments minus rewards paid) |
| Covariates logged at sign-up | Country tier, device and OS, acquisition channel, sign-up hour and weekday |
| Decision rule | Ship if the always-valid 95% interval for the lift is entirely above zero and the guardrail is not breached. Don't ship if it is entirely below zero. Otherwise keep collecting up to a pre-set maximum sample, then report "inconclusive". |

Note on timing: activation takes 72 hours to observe. On screen, a player enters the analysis when their 72-hour window closes.

## 3. What the visitor sees

One screen with two halves: what happens to players, and what the analyst concludes from it. The statistics are shown as the summary of the behaviour above them.

### 3.1 Player view

1. **The two experiences.** What a control player and a Starter Bonus player see, side by side. Always visible.
2. **Players arriving.** Two lanes, control and treatment. Each refresh drops in dots, filled if the player completed the first milestone. A dot stands for a group of players when batches are large (for example one dot per 40 players).
3. **One player's story (on tap only).** Tapping a dot opens one sampled player's journey: profile, sign-up time, assigned arm, started a game, reached the milestone, counted in the analysis.

| Source | Player story |
|---|---|
| Synthetic personas | Rich: full profile, journey with timings, and the persona's own stated reason (section 5) |
| Simulator | Generated from a simple behaviour model (time to start, time to milestone) |

### 3.2 Analyst view

Three layers. Everything beyond the first two is behind a "details" toggle.

1. **Verdict.** A single status: *Keep collecting*, *Ship*, or *Don't ship*, with one plain sentence underneath that updates ("After 6,200 players the Starter Bonus is ahead by 1.8 points, but that could still be noise").
2. **Evidence.** One chart: the estimated lift over time with its interval narrowing, and a zero line.
3. **Details (toggle).** Naive vs always-valid interval side by side, sample-ratio check, covariate balance table, effect by segment.

### 3.3 Controls and navigation

- Controls: play / pause, speed (1×, 5×, skip to end), and a data-source switch (Simulator / Synthetic personas).
- Section bar with two entries: "Live experiment" (this page) and "After the experiment" (end-of-run readout and the targeting article, section 8).
- Visible by default: the two experiences, the arriving players, the verdict and the chart. Nothing else. The player story and the details open on request.

## 4. Data source 1: Simulator (known truth)

- The visitor picks a preset first: *No effect*, *Small real effect*, *Large effect*. Sliders come second, three at most: true lift, baseline rate, traffic.
- A "reveal truth" toggle shows the true lift as a line on the chart.
- A "run 200 parallel worlds" button shows how often each method raises a false alarm and how often its interval covers the truth.
- Each simulated player has covariates drawn from a fixed population, an arm from the hash rule, an outcome, and a journey (time to start, time to milestone) from a simple behaviour model.
- The data-generating process lives in one documented config file: covariate distributions, how baseline activation depends on covariates, the true lift, and any designed-in difference in lift between segments.

Starting values, to be tuned by simulation: baseline activation 22%; presets of 0, +2 and +5 percentage points.

## 5. Data source 2: Synthetic personas (recorded run)

- Each unit is one independent model call. A persona is drawn (age band, country tier, device, casual vs regular player, plays for fun vs for earnings, time available), assigned to control or treatment by hash, shown the Questline onboarding with or without the Starter Bonus, and asked what it would do.
- Generated once, offline, by a script in this repository, and shipped as a static log. The page replays it. Nothing on the page calls a model.
- Label on screen: "recorded run, replayed", with model name and date.
- Each call returns a structured record:
  - Profile: the randomized attributes plus a short backstory (what they do, when they play, what games they like).
  - Journey: whether they start a game, how long until they start, whether they reach the first milestone, how long that takes.
  - Reason: one sentence in the persona's own words.
- The randomized attributes are the covariates. The backstory is colour only and is not used in the analysis.
- The verdict uses only the yes / no outcome. Timings are the persona's stated journey, shown for the story. Comparing time-to-milestone between arms among those who completed is descriptive, not causal.
- Pool: about 5,000 units per experiment (about 20,000 if the targeting article in section 8 uses it). At least two experiments: the Starter Bonus test and an A/A test.
- Each visit replays a different random order of the pool.
- Stated limitation, shown on the page: this measures how the model responds, not how people do.

**Gate before full generation:** run a pilot of about 200 calls and report the outcome rate per arm and how much responses vary. If nearly all personas give the same answer, stop and revise the prompt with Daniel before spending more.

**Cost and keys:** the generation script reads the API key from an environment variable. No key is committed or shipped to the browser. The script takes a hard cap on the number of calls.

## 6. The live stream

- The page refreshes every 2 to 3 seconds (small random jitter). Each refresh is one "hour" of the experiment and brings a batch of players, with batch size drawn from a Poisson distribution.
- Each visit uses a new random seed, so the order, the path of the estimate and the stopping point differ from visit to visit.
- The seed is in the URL, so any run can be shared and reproduced exactly. Use a seeded generator, never `Math.random()`.
- Target: the default preset reaches a verdict in 60 to 90 seconds at normal speed. Batch size and refresh length are tuned by simulation to hit this.

## 7. Statistics engine

Computed on every refresh, from running totals only (counts, sums, sums of squares):

- Difference in proportions (and in means, for the guardrail) with a standard fixed-horizon interval and p-value. Shown as the "naive" method.
- Always-valid confidence sequence and p-value. This drives the verdict. Default: two-sided, 95%. Reuse the implementation from Vega or Lyra if one exists and is tested; otherwise propose a method in the reuse report.
- Sample-ratio mismatch check.
- Covariate balance table.
- Effect by segment: the lift within a few segments fixed in advance (three at most, for example country tier, device, acquisition channel), from running totals per segment, with the always-valid interval widened for the number of segment levels shown. Framed as monitoring ("is any group being harmed?"), not as a search for winners.
- Phase 2: regression adjustment with sign-up covariates, and the guardrail metric.

**Where it runs.** In the browser. No API, server or database. Every quantity above is closed-form arithmetic on running totals. Python is the reference implementation; the browser code is a port of it.

**Assignment.** hash(player ID + experiment key) gives a number between 0 and 1; below 0.5 means treatment. Covariates play no part in assignment. They are logged at arrival and used only in the analysis.

**Required evidence of validity (kept in the repository and summarised on the page):**

1. Under no effect, with the result checked on every refresh up to the maximum sample, the always-valid method declares a winner in at most 5% of at least 2,000 simulated runs (within simulation error).
2. Under each preset, the always-valid interval contains the true lift at every refresh in at least 95% of runs.
3. The naive method's false-alarm rate under the same continuous checking is reported next to it.
4. The browser port and the Python reference return the same numbers on shared test fixtures, to a tight numerical tolerance.

## 8. After the experiment

A separate section reached from the section bar. Computed offline; nothing here updates live.

- **End-of-run readout.** A short plain-language summary of the run the visitor just watched: decision, lift and interval, sample size, checks passed.
- **Targeting article.** Once the ship decision is made, a second question follows: ship to whom? The Starter Bonus costs money, so it should go where the lift exceeds the cost. This is policy learning, done once on the final sample.
  - Format: an article or notebook rendered as a page.
  - Method: a causal forest fitted offline in Python. On simulator data the true effect per segment is known, so estimated effects are plotted against true ones. On persona data the truth is unknown.
  - Output: a ranked list of segments or a shallow tree, plus the gain from targeting.
  - Safeguards: covariates fixed in advance; honest sample splitting; an overall test of whether effects differ at all before any segment is shown; a plain pre-specified subgroup comparison as the baseline the forest has to beat.

## 9. Design direction

- Simple, calm and good-looking. A visitor with no statistics background should understand the page in ten seconds.
- Reference for layout and feel: the results view of Spotify's Confidence (clean rows of metrics with interval bars). Take inspiration only; use own name, colours and branding.
- **Not a second Vega or Lyra.** Do not reuse their interface, navigation or visual style. Lyra in particular is hard to navigate and overwhelming; this project is the opposite.
- One accent colour plus neutrals. Generous whitespace. The verdict is the largest element on the screen.
- Plain-language captions that update with the data. No jargon above the "details" toggle.
- Motion is subtle and purposeful: dots arriving, the interval narrowing.
- Works on a phone and on a laptop. Light and dark themes. Readable contrast.
- No walls of cards, no dense dashboards, no settings panels on the main screen.

## 10. Extras

- **Your run vs all runs.** A histogram of stopping times across 1,000 pre-computed runs, with the visitor's run marked.
- **Peeking counter.** Shows the first moment the naive method would have declared a winner, next to what the valid method says at that moment.

## 11. Honest labels, scope and open decisions

**Labels shown on the page**

- Questline is fictional; simulator data is generated.
- Persona runs are recorded model responses, not human behaviour.
- In an A/A run, a small share of visitors will see a false "ship". That share is the stated error rate, and the page shows it.

**Out of scope**

- Any backend, database, login or live model call from the page.
- Real visitor traffic as experimental data.
- Real-data replay (Cookie Cats and similar): considered and dropped.
- Refitting heavy models (causal forests) in the browser.
- Adaptive assignment or bandits.

**Open decisions**

| # | Decision | Default if Daniel has not said otherwise |
|---|---|---|
| 1 | Product name and fictional company name | Keep the working names |
| 2 | Technology stack | Propose in the reuse report; must build to a static site |
| 3 | Always-valid method and tuning | Reuse the Vega or Lyra one if tested; otherwise propose in the reuse report |
| 4 | Refresh length, batch size, maximum sample | Tune by simulation to the 60 to 90 second target |
| 5 | Model for the personas and budget | No default: ask Daniel |
| 6 | Segments in the live table | Country tier, device, acquisition channel |
| 7 | Hosting | No default: ask Daniel |
| 8 | Whether the targeting article is built | Yes, last |

## 12. Milestones

Stop for review after each one.

| # | Milestone | Done when |
|---|---|---|
| 0 | Read Vega and Lyra; reuse report; proposed stack | `docs/vega-reuse.md` covers both and Daniel has approved it |
| 1 | Python reference engine and tests | Validity evidence 1 to 3 in section 7 is produced by a script and passes |
| 2 | Browser port of the engine | Parity tests against the Python reference pass (evidence 4) |
| 3 | Simulator stream and analyst view | A run plays from a URL seed to a verdict; verdict, chart and details toggle work; play, pause and speed work |
| 4 | Player view | Two experiences, arriving players, and the story on tap are in place; the default screen shows only the four agreed elements |
| 5 | Simulator controls and extras | Presets, sliders, reveal truth, parallel worlds, peeking counter, your run vs all runs |
| 6 | Design pass | Reviewed against section 9 on phone and laptop, light and dark |
| 7 | Persona pilot | 200-call pilot report delivered; Daniel approves the prompt and budget |
| 8 | Persona source | Full recorded runs generated; replay works with rich player stories |
| 9 | Phase 2 statistics | Live segment table, guardrail metric, regression adjustment |
| 10 | After the experiment | Readout page and targeting article |

## References

- Confidence by Spotify (look and feel reference): https://confidence.spotify.com/
- Confidence sequences library (`confseq`): https://pypi.org/project/confseq/0.0.2/
- Statsig sequential testing documentation: https://docs.statsig.com/experiments/advanced-setup/sequential-testing
- Netflix, rapid regression detection through sequential testing: https://ar5iv.labs.arxiv.org/html/2205.14762
- Prior art, simulated stream with always-valid inference: https://github.com/t4rantul777/ab-testing-platform
