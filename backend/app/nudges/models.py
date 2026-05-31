"""Public models for the nudge engine."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NudgeCTA(BaseModel):
    label: str
    route: str


class Nudge(BaseModel):
    id: str
    rule_id: str
    category: str
    title: str
    body: str
    cta: Optional[NudgeCTA] = None
    priority: float = 0.0
    emitted_at: datetime


class RuleStats(BaseModel):
    shown: int = 0
    engaged: int = 0


class NudgeContext(BaseModel):
    """Context handed to each rule's `evaluate` method.

    Rules read only; they never mutate state.
    """

    model_config = {"arbitrary_types_allowed": True}

    entries: list  # list[Entry] — kept untyped to avoid import cycle
    state: "NudgeState"
    prefs: "Preferences"
    now: datetime


# Forward refs resolved at import time after siblings exist
from .state import NudgeState  # noqa: E402
from .preferences import Preferences  # noqa: E402

NudgeContext.model_rebuild()
