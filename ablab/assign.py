"""Hash assignment: MurmurHash3 (32-bit) of 'player_id:experiment_key', scaled to [0, 1).

The browser port must reproduce these numbers exactly (fixtures/assign.json).
"""

from __future__ import annotations

from collections.abc import Iterable

import mmh3
import numpy as np


def assignment_u(player_id: str, key: str) -> float:
    return mmh3.hash(f"{player_id}:{key}", 0, signed=False) / 2**32


def assignment_us(player_ids: Iterable[str], key: str) -> np.ndarray:
    return np.array([assignment_u(pid, key) for pid in player_ids])


def is_treated(u: float | np.ndarray, share: float = 0.5):
    """Below the treatment share means Starter Bonus."""
    return u < share
