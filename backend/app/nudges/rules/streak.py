"""Streak celebration rule — never loss-framed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from ..models import Nudge, NudgeContext


MILESTONES = {3, 7, 14, 30, 60, 100}


def _current_streak(entries, today) -> int:
    days = {e.timestamp.date() for e in entries}
    streak = 0
    d = today
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


@dataclass
class StreakRule:
    id: str = "streak"
    category: str = "streak"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        if not ctx.entries:
            return None
        today = ctx.now.date()
        streak = _current_streak(ctx.entries, today)
        if streak in MILESTONES:
            return Nudge(
                id=str(uuid4()),
                rule_id=self.id,
                category=self.category,
                title=f"{streak}-day streak!",
                body=f"You've logged {streak} days in a row. Nice rhythm.",
                emitted_at=ctx.now,
            )
        return None


RULE = StreakRule()
