"""Algorithm unit tests."""

from __future__ import annotations

import random
from datetime import datetime, time, timezone

import pytest

from app.nudges.algorithms.bandit import select
from app.nudges.algorithms.change_point import detect_recent_shift
from app.nudges.algorithms.von_mises_timing import compute_optimal_reminder
from app.nudges.models import Nudge
from app.nudges.state import NudgeState, RuleStats


UTC = timezone.utc


def test_von_mises_returns_fallback_below_threshold():
    fb = time(9, 0)
    assert compute_optimal_reminder([8, 8, 8], fb) == fb


def test_von_mises_picks_modal_hour():
    fb = time(9, 0)
    hours = [8, 8, 9, 8, 8, 8, 8, 9, 7, 8]
    out = compute_optimal_reminder(hours, fb)
    assert abs(out.hour - 8) <= 1


def test_cusum_detects_planted_down_shift():
    series = [4.0] * 10 + [2.0] * 7
    shift = detect_recent_shift(series, window=5)
    assert shift is not None
    assert shift.direction == "down"
    assert shift.magnitude >= 1.5


def test_cusum_no_shift_on_flat():
    series = [3.0] * 20
    assert detect_recent_shift(series, window=5) is None


def _make_nudge(rule_id: str) -> Nudge:
    return Nudge(
        id=f"id-{rule_id}",
        rule_id=rule_id,
        category=rule_id,
        title=rule_id,
        body="",
        emitted_at=datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
    )


def test_bandit_prefers_higher_engagement_arm():
    state = NudgeState(
        rule_stats={
            "A": RuleStats(shown=20, engaged=15),
            "B": RuleStats(shown=20, engaged=2),
        }
    )
    now = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    wins_A = 0
    for seed in range(100):
        rng = random.Random(seed)
        chosen = select([_make_nudge("A"), _make_nudge("B")], state, now, rng=rng)
        if chosen.rule_id == "A":
            wins_A += 1
    assert wins_A >= 85
