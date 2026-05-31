"""Change-point reflection rule — curious, never diagnostic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from ..algorithms.change_point import detect_recent_shift
from ..models import Nudge, NudgeContext


@dataclass
class ChangePointReflectionRule:
    id: str = "change_point"
    category: str = "change_point"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        if len(ctx.entries) < 10:
            return None
        # Sorted oldest -> newest
        ordered = sorted(ctx.entries, key=lambda e: e.timestamp)
        series = [float(e.mood) for e in ordered]
        shift = detect_recent_shift(series, window=5, threshold=0.8)
        if shift is None:
            return None
        return Nudge(
            id=str(uuid4()),
            rule_id=self.id,
            category=self.category,
            title="Noticed a shift this week",
            body="Something looks different in your recent entries — want to note what changed?",
            cta={"label": "Reflect", "route": "/log"},
            emitted_at=ctx.now,
        )


RULE = ChangePointReflectionRule()
