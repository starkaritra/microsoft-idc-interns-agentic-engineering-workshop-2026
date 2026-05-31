"""Reminder rule — fires at user's typical logging hour."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Optional
from uuid import uuid4

from ..algorithms.von_mises_timing import compute_optimal_reminder
from ..models import Nudge, NudgeContext


@dataclass
class ReminderRule:
    id: str = "reminder"
    category: str = "reminder"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        # If user already logged today, skip.
        today = ctx.now.date()
        if any(e.timestamp.date() == today for e in ctx.entries):
            return None

        # Determine optimal hour
        override = ctx.prefs.reminder_time_override
        if override:
            target = time.fromisoformat(override)
        else:
            hours = [e.timestamp.hour for e in ctx.entries]
            target = compute_optimal_reminder(hours, fallback=time(9, 0))

        # Fire within +/- 30 min of target
        now_minutes = ctx.now.hour * 60 + ctx.now.minute
        target_minutes = target.hour * 60 + target.minute
        if abs(now_minutes - target_minutes) > 30:
            return None

        return Nudge(
            id=str(uuid4()),
            rule_id=self.id,
            category=self.category,
            title="Time for your check-in",
            body="Take a moment to log how you're feeling.",
            cta={"label": "Log entry", "route": "/log"},
            emitted_at=ctx.now,
        )


RULE = ReminderRule()
