"""Load config/simulator.toml, the single source for the simulated world, the plan and the page."""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "simulator.toml"


@cache
def load(path: Path | str = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)
