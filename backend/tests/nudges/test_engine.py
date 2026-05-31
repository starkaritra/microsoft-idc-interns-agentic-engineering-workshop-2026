"""Tests for compute_nudges + each rule."""

from __future__ import annotations

import random
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.entry import Entry
from app.nudges.engine import compute_nudges
from app.nudges.preferences import Preferences, QuietHours
from app.nudges.state import NudgeState, RuleStats


UTC = timezone.utc


def make_entry(ts: datetime, mood: int = 4, energy: int = 6, tags: list[str] | None = None) -> Entry:
    return Entry(
        id=str(uuid4()),
        mood=mood,
        energy=energy,
        note=None,
        tags=tags or [],
        timestamp=ts,
    )


def default_prefs(**overrides) -> Preferences:
    # Disable change_point by default per spec
    return Preferences(
        quiet_hours=QuietHours(start="22:00", end="06:00"),
        **overrides,
    )


def empty_state() -> NudgeState:
    return NudgeState()


# Slice 1
def test_engine_returns_empty_for_new_user():
    now = datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
    assert compute_nudges([], empty_state(), default_prefs(), now) == []


# Slice 4 — onboarding shield
def test_no_nudges_before_three_entries():
    now = datetime(2026, 5, 31, 9, 0, tzinfo=UTC)
    entries = [make_entry(now - timedelta(days=i, hours=1)) for i in range(2)]
    assert compute_nudges(entries, empty_state(), default_prefs(), now) == []


# Slice 2 — reminder fires at typical hour
def test_reminder_fires_at_typical_logging_hour():
    now_at_8 = datetime(2026, 5, 31, 8, 0, tzinfo=UTC)
    # 10 entries all at 08:00 over past 11 days (skip today)
    entries = [
        make_entry(datetime(2026, 5, 30 - i, 8, 0, tzinfo=UTC)) for i in range(10)
    ]
    prefs = default_prefs()
    # Isolate reminder rule (missing_entry would also fire after ~24h gap)
    prefs.categories_enabled["missing_entry"] = False
    prefs.categories_enabled["streak"] = False
    prefs.categories_enabled["pattern"] = False
    out = compute_nudges(entries, empty_state(), prefs, now_at_8)
    assert len(out) == 1
    assert out[0].rule_id == "reminder"

    now_at_14 = datetime(2026, 5, 31, 14, 0, tzinfo=UTC)
    out_2 = compute_nudges(entries, empty_state(), prefs, now_at_14)
    assert all(n.rule_id != "reminder" for n in out_2)


# Slice 3 — quiet hours suppress
def test_quiet_hours_suppress_everything():
    now = datetime(2026, 5, 31, 8, 0, tzinfo=UTC)
    entries = [
        make_entry(datetime(2026, 5, 30 - i, 8, 0, tzinfo=UTC)) for i in range(10)
    ]
    prefs = Preferences(quiet_hours=QuietHours(start="07:00", end="10:00"))
    assert compute_nudges(entries, empty_state(), prefs, now) == []


# Slice 5 — missing entry
def test_missing_entry_after_25h():
    now = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    last_ts = now - timedelta(hours=25)
    entries = [
        make_entry(last_ts),
        make_entry(last_ts - timedelta(days=1)),
        make_entry(last_ts - timedelta(days=2)),
    ]
    # Reminder relies on optimal hour from <7 samples => fallback 09:00, won't fire at 12:00.
    # Disable categories that would conflict so missing_entry is the only candidate.
    prefs = default_prefs()
    prefs.categories_enabled["reminder"] = False
    out = compute_nudges(entries, empty_state(), prefs, now)
    assert len(out) == 1
    assert out[0].rule_id == "missing_entry"


# Slice 6 — streak celebrates without loss framing
def test_streak_milestone_seven_days():
    now = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    entries = [make_entry(datetime(2026, 5, 31 - i, 10, 0, tzinfo=UTC)) for i in range(7)]
    prefs = default_prefs()
    # Disable other categories to isolate streak
    for k in ("reminder", "missing_entry", "first_insight", "pattern"):
        prefs.categories_enabled[k] = False
    out = compute_nudges(entries, empty_state(), prefs, now)
    assert len(out) == 1
    assert out[0].rule_id == "streak"
    assert "7" in out[0].title
    banned = ("broke", "lost", "missed")
    text = (out[0].title + " " + out[0].body).lower()
    assert not any(b in text for b in banned)


# Slice 7 — first insight one-shot
def test_first_insight_one_shot():
    now = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    entries = [make_entry(datetime(2026, 5, 31 - i, 10, 0, tzinfo=UTC)) for i in range(7)]
    prefs = default_prefs()
    for k in ("reminder", "missing_entry", "streak", "pattern"):
        prefs.categories_enabled[k] = False
    state = empty_state()
    out = compute_nudges(entries, state, prefs, now)
    assert len(out) == 1 and out[0].rule_id == "first_insight"

    state.one_shot_fired.append("first_insight")
    out2 = compute_nudges(entries, state, prefs, now)
    assert out2 == []


# Slice 18 — engine cap = 1
def test_engine_never_returns_more_than_one():
    now = datetime(2026, 5, 31, 8, 0, tzinfo=UTC)
    entries = [
        make_entry(datetime(2026, 5, 30 - i, 8, 0, tzinfo=UTC), mood=4, tags=["exercise"])
        for i in range(15)
    ]
    out = compute_nudges(entries, empty_state(), default_prefs(), now)
    assert len(out) <= 1
