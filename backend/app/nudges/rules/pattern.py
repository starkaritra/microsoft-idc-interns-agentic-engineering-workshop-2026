"""Pattern rule — fires when a tag correlates with mood lift (perm-test gated)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from ..models import Nudge, NudgeContext


MIN_TAGGED_DAYS = 10
MIN_DELTA = 0.5
P_VALUE_THRESHOLD = 0.05
N_PERMUTATIONS = 1000


def _per_day(entries):
    by_day: dict = {}
    for e in entries:
        d = e.timestamp.date()
        by_day.setdefault(d, []).append(e)
    out = []
    for d, es in by_day.items():
        avg_mood = sum(x.mood for x in es) / len(es)
        tags = set()
        for x in es:
            tags.update(x.tags or [])
        out.append((d, avg_mood, tags))
    return out


def _best_pattern(entries, rng_seed: int = 0):
    days = _per_day(entries)
    if len(days) < MIN_TAGGED_DAYS * 2:
        return None
    all_tags: set = set()
    for _, _, t in days:
        all_tags.update(t)

    import numpy as np

    rng = np.random.default_rng(rng_seed)
    best = None
    for tag in all_tags:
        with_t = [m for _, m, ts in days if tag in ts]
        without_t = [m for _, m, ts in days if tag not in ts]
        if len(with_t) < MIN_TAGGED_DAYS or len(without_t) < 3:
            continue
        delta = float(np.mean(with_t) - np.mean(without_t))
        if abs(delta) < MIN_DELTA:
            continue

        moods = np.array([m for _, m, _ in days])
        n_with = len(with_t)
        observed_abs = abs(delta)
        # Permutation: shuffle which days are "with tag"
        count_extreme = 0
        for _ in range(N_PERMUTATIONS):
            idx = rng.permutation(len(moods))
            sample_with = moods[idx[:n_with]].mean()
            sample_without = moods[idx[n_with:]].mean()
            if abs(sample_with - sample_without) >= observed_abs:
                count_extreme += 1
        p = (count_extreme + 1) / (N_PERMUTATIONS + 1)
        if p < P_VALUE_THRESHOLD:
            if best is None or abs(delta) > abs(best[1]):
                best = (tag, delta, p)
    return best


@dataclass
class PatternRule:
    id: str = "pattern"
    category: str = "pattern"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        # Use a deterministic seed from `now` so repeated calls in same minute agree
        seed = int(ctx.now.timestamp()) // 60
        result = _best_pattern(ctx.entries, rng_seed=seed)
        if result is None:
            return None
        tag, delta, _p = result
        direction = "higher" if delta > 0 else "lower"
        return Nudge(
            id=str(uuid4()),
            rule_id=self.id,
            category=self.category,
            title=f"Pattern: {tag}",
            body=f"On days you logged '{tag}', your mood was {abs(delta):.1f} points {direction} on average.",
            emitted_at=ctx.now,
        )


RULE = PatternRule()
