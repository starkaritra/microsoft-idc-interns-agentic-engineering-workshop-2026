"""First-insight one-shot at entry #7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from ..models import Nudge, NudgeContext


@dataclass
class FirstInsightRule:
    id: str = "first_insight"
    category: str = "first_insight"

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]:
        if self.id in ctx.state.one_shot_fired:
            return None
        if len(ctx.entries) < 7:
            return None

        moods = [e.mood for e in ctx.entries]
        avg = sum(moods) / len(moods)
        return Nudge(
            id=str(uuid4()),
            rule_id=self.id,
            category=self.category,
            title="Your first insight is ready",
            body=f"You've logged {len(ctx.entries)} entries. Your average mood so far is {avg:.1f}/5 — open the dashboard to explore patterns.",
            cta={"label": "See dashboard", "route": "/"},
            emitted_at=ctx.now,
        )


RULE = FirstInsightRule()
