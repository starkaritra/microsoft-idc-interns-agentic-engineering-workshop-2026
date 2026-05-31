"""NudgeRule protocol."""

from __future__ import annotations

from typing import Optional, Protocol

from ..models import Nudge, NudgeContext


class NudgeRule(Protocol):
    id: str
    category: str

    def evaluate(self, ctx: NudgeContext) -> Optional[Nudge]: ...
