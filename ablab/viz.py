"""Shared figure style for notebooks and article figures. Colours match docs/design.md."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

CONTROL = "#4a5260"   # standard rewards
TREAT = "#d99a0b"     # Starter Bonus
INK = "#15181e"
MUTED = "#5b6270"
LINE = "#e2e5ea"
SHIP = "#1f8a4c"
STOP = "#c2362f"
ARM_COLORS = {"control": CONTROL, "treatment": TREAT}

# Sequential: page background to gold to deep amber. Diverging: control grey, neutral, gold.
GOLD_CMAP = LinearSegmentedColormap.from_list("ablab_gold", ["#f5f6f8", "#f6dd9c", TREAT, "#6b4700"])
DIVERGING_CMAP = LinearSegmentedColormap.from_list("ablab_div", [CONTROL, "#f5f6f8", TREAT])

FIGURES = Path(__file__).resolve().parent.parent / "figures"


def use_style() -> None:
    """Apply the project style. Call once at the top of a notebook."""
    plt.style.use(Path(__file__).with_name("ablab.mplstyle"))


def savefig(fig, name: str) -> None:
    """Save to figures/<name>.png and .svg (SVG for the blog, PNG for previews), then show it."""
    FIGURES.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURES / f"{name}.{ext}")
    plt.show()
