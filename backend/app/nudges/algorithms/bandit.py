"""Thompson sampling bandit with time-decay across nudge candidates."""

from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Optional

DEFAULT_TAU_HOURS = 24.0


def _beta_sample(rng: random.Random, alpha: float, beta: float) -> float:
    return rng.betavariate(alpha, beta)


def select(
    candidates: list,
    state,
    now: datetime,
    rng: Optional[random.Random] = None,
    decay_tau_hours: float = DEFAULT_TAU_HOURS,
):
    """Pick the candidate with the highest Thompson * decay score.

    `candidates`: list of Nudge instances.
    `state`: NudgeState (used for per-rule rule_stats + last_shown_at).
    `rng`: random.Random for determinism. If None, uses module random.
    """
    if not candidates:
        return None
    if rng is None:
        rng = random.Random()

    best = None
    best_score = -1.0
    for nudge in candidates:
        stats = state.rule_stats.get(nudge.rule_id)
        if stats is None:
            shown, engaged = 0, 0
        else:
            shown, engaged = stats.shown, stats.engaged
        alpha = engaged + 1.0
        beta = max(0, shown - engaged) + 1.0
        theta = _beta_sample(rng, alpha, beta)

        last = state.last_shown_at.get(nudge.rule_id)
        if last is None:
            decay = 1.0
        else:
            dt_hours = max(0.0, (now - last).total_seconds() / 3600.0)
            # Recent shows -> suppress (we want time *since* last to grow)
            # Score is suppressed when dt small, recovers as dt grows.
            decay = 1.0 - math.exp(-dt_hours / decay_tau_hours)

        score = theta * decay if last is not None else theta
        if score > best_score:
            best_score = score
            best = nudge
            best.priority = float(score)
    return best
