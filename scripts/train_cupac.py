"""Train the CUPAC model on an earlier cohort and write config/cupac.json (notebook 06).

    python -m scripts.train_cupac
"""

from __future__ import annotations

import json

from ablab.cupac import CUPAC_PATH, train
from ablab.simulator import simulate

COHORT_SEED = 20261019  # notebook 06's earlier cohort


def main():
    cohort, _ = simulate(0.0, seed=COHORT_SEED)  # before the test: standard rewards for everyone
    m = train(cohort)
    m["cohort_seed"] = COHORT_SEED
    CUPAC_PATH.write_text(json.dumps(m, indent=2))
    print(f"wrote {CUPAC_PATH.name}: theta {m['theta']:.3f}, mu {m['mu']:.4f}, holdout R² {m['r2_holdout']:.3f}")


if __name__ == "__main__":
    main()
