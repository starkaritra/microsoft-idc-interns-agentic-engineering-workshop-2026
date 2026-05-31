"""Nudge engine composition — pure function."""

from __future__ import annotations

import random
from datetime import datetime, time, timedelta
from typing import Optional

from .algorithms import bandit
from .algorithms.skip_predictor import probability_of_no_entry_today
from .models import Nudge, NudgeContext
from .preferences import Preferences
from .rules import ALL_RULES
from .state import NudgeState


ONBOARDING_MIN_ENTRIES = 3
SKIP_SUPPRESSION_THRESHOLD = 0.4  # if P(no entry) < 0.4, suppress reminder
DISMISS_DECAY_HOURS = 24


def _in_quiet_hours(now_time: time, start_s: str, end_s: str) -> bool:
    start = time.fromisoformat(start_s)
    end = time.fromisoformat(end_s)
    if start == end:
        return False
    if start < end:
        return start <= now_time < end
    # wraps midnight
    return now_time >= start or now_time < end


def compute_nudges(
    entries: list,
    state: NudgeState,
    prefs: Preferences,
    now: datetime,
    rng: Optional[random.Random] = None,
) -> list[Nudge]:
    """Return 0 or 1 nudges. Pure: no I/O, no state mutation."""

    # Onboarding shield
    if len(entries) < ONBOARDING_MIN_ENTRIES:
        return []

    # Quiet hours
    if _in_quiet_hours(now.time(), prefs.quiet_hours.start, prefs.quiet_hours.end):
        return []

    ctx = NudgeContext(entries=entries, state=state, prefs=prefs, now=now)

    candidates: list[Nudge] = []
    for rule in ALL_RULES:
        # Category gate
        if not prefs.categories_enabled.get(rule.category, False):
            continue
        # Snooze gate
        snooze_until = state.snoozed_until.get(rule.id)
        if snooze_until and now < snooze_until:
            continue
        # Recent dismissal gate
        dismissed = state.dismissed_at.get(rule.id)
        if dismissed and (now - dismissed) < timedelta(hours=DISMISS_DECAY_HOURS):
            continue

        nudge = rule.evaluate(ctx)
        if nudge is None:
            continue

        # Skip-predictor: applies only to reminder
        if rule.id == "reminder":
            p_no_entry = probability_of_no_entry_today(entries, now)
            if p_no_entry < SKIP_SUPPRESSION_THRESHOLD:
                continue

        candidates.append(nudge)

    if not candidates:
        return []

    selected = bandit.select(candidates, state, now, rng=rng)
    if selected is None:
        return []
    return [selected]
