# Notebooks

Every model starts here. A notebook explains the method, looks at the data, and shows the results in figures. Once Daniel has reviewed it, the code is promoted into the `ablab` package with tests, and the notebook switches to importing it.

## Life of a notebook

1. **Explore.** Write the model and the code inline in the notebook.
2. **Review.** Daniel reads it, checks the figures and the results.
3. **Promote.** Functions move to `ablab/`, with pytest tests in `tests/`. Validity numbers are written to `results/*.json`, which is what the page cites.
4. **Parity.** The notebook keeps its readable code (it is also blog material) and gains a final *Production parity* cell that asserts `ablab` reproduces its results exactly. Re-run it top to bottom; if production drifts, that cell fails.

A notebook is never imported by production code. The page never shows a number that only exists in a notebook.

## Sections in every notebook

Copy [_template.ipynb](_template.ipynb).

1. **Question.** One or two sentences: what this notebook decides.
2. **Model.** The equations in LaTeX, with each symbol defined once. Not a full article, just enough to see what happens behind the scenes. Link the relevant note in [docs/theory/](../docs/theory/).
3. **Libraries.** Which Python libraries do the work, and which parts we write ourselves.
4. **Data.** Generate or load it. Show its shape and a few rows.
5. **Descriptives.** Summary tables, distributions, balance.
6. **Figures.** Time series, heatmaps, distributions. Saved with `savefig()` to `figures/` as PNG and SVG, ready for blog articles.
7. **Results.** What the numbers say, against the threshold set in the brief.
8. **What gets promoted.** Which functions move to `ablab/`, and which tests guard them.

## Conventions

- Names: `NN_topic.ipynb`, numbered in reading order.
- Paired with a jupytext `.py` (percent format) so diffs and reviews stay readable. `jupytext --sync notebooks/*.ipynb` after editing.
- Figures: `from ablab.viz import use_style, savefig, CONTROL, TREAT`. Control is grey, Starter Bonus is gold, same as the page.
- Every random draw is seeded, and the seed is printed near the top.
- Long simulations cache results to `results/` so re-running the notebook is quick.

## Planned notebooks

| # | Notebook | Milestone | Decides |
|---|---|---|---|
| 01 | `01_players_and_dgp` | M1 | The simulated population: covariates, baseline activation, presets, arrivals |
| 02 | `02_peeking_problem` | M1 | Why the usual interval fails under continuous checking |
| 03 | `03_always_valid` | M1 | The confidence sequence and p-value, ρ² tuning, validity evidence 1–3 |
| 04 | `04_power_and_planning` | M1 | Break-even lift, sample size (fixed and sequential), max sample, tick length for a 60–90 s verdict |
| 05 | `05_checks_and_segments` | M9 | SRM, balance, segment intervals with widening |
| 06 | `06_regression_adjustment` | M9 | CUPED / Lin adjustment and the guardrail |
| 07 | `07_persona_pilot` | M7 | The 200-call pilot report |
| 08 | `08_targeting` | M10 | Causal forest, honest splitting, gain from targeting |
