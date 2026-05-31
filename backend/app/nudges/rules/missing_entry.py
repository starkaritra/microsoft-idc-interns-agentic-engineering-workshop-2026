"""Missing-entry rule — fires when > 24h since last entry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from ..models import Nudge, NudgeContext


@dataclass
class MissingEntryRule:
    id: str = "missing_entry"
    category: str = "missing_entry"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        if len(ctx.entries) < 3:
            return None
        latest = max(e.timestamp for e in ctx.entries)
        delta = ctx.now - latest
        if delta < timedelta(hours=24):
            return None
        return Nudge(
            id=str(uuid4()),
            rule_id=self.id,
            category=self.category,
            title="Quick check-in?",
            body="It's been a day since your last entry. A 10-second log helps the trends stay accurate.",
            cta={"label": "Log entry", "route": "/log"},
            emitted_at=ctx.now,
        )


RULE = MissingEntryRule()
