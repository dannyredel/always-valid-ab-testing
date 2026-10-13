# CLAUDE.md

Read [docs/brief.md](docs/brief.md) first. It is the source of truth for scope.

## Rules

- Vega (`../Vega`) and Lyra (`../Vega/lyra`) are **read-only**. Copy what is reused into this repo; never import from them.
- Reuse logic and theory, not interface. This page must not look or navigate like Vega or Lyra.
- Work in milestones (brief §12, [BACKLOG.md](BACKLOG.md)). Stop for review at the end of each with a note in [LOG.md](LOG.md): what was built, how it was verified, deviations.
- No invented numbers on the page. Every validity claim needs a test or simulation in the repo.
- Seeded RNG only. Never `Math.random()` in product code.
- Ask before settling anything in [DECISIONS.md](DECISIONS.md) that has no default, and before adding scope.
- Design rules live in [docs/design.md](docs/design.md). Default screen shows four elements; everything else is behind a tap or toggle.

## Notebook-first

- Every model starts as a notebook in `notebooks/`, following [notebooks/README.md](notebooks/README.md): LaTeX model, libraries, data, descriptives, figures, results, what gets promoted.
- Daniel reviews the notebook before anything moves to `ablab/`. Promoted code gets pytest tests, and the notebook gets a final *Production parity* cell asserting `ablab` reproduces it.
- All parameters live in `config/simulator.toml`. Run `python -m pytest`, `python -m validity.always_valid` and `python -m scripts.make_fixtures` after changing the engine.
- Figures use `ablab.viz` (control grey, Starter Bonus gold) and are saved to `figures/` for blog articles.

## Housekeeping

- Log every session in LOG.md (newest first).
- Tick tasks in BACKLOG.md as they finish.
