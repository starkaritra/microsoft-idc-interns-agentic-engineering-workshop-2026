"""Rule registry."""

from __future__ import annotations

from .reminder import RULE as REMINDER
from .missing_entry import RULE as MISSING_ENTRY
from .first_insight import RULE as FIRST_INSIGHT
from .streak import RULE as STREAK
from .pattern import RULE as PATTERN
from .change_point_reflection import RULE as CHANGE_POINT


ALL_RULES = [
    REMINDER,
    MISSING_ENTRY,
    FIRST_INSIGHT,
    STREAK,
    PATTERN,
    CHANGE_POINT,
]
