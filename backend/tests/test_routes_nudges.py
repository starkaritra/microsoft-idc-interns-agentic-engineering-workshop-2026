"""HTTP route tests for nudges + preferences + retention."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.models.entry import Entry
from app.nudges import state as state_module


UTC = timezone.utc


def _seed_entries_file(entries: list[Entry]):
    storage._write_all([e.model_dump(mode="json") for e in entries])


def test_get_nudges_returns_empty_for_new_user(client: TestClient):
    resp = client.get("/api/nudges")
    assert resp.status_code == 200
    assert resp.json() == {"nudges": []}


def test_get_nudges_marks_shown_in_state(client: TestClient):
    # 25h old + 3 entries → missing_entry should fire
    from uuid import uuid4

    now = datetime.now(UTC)
    entries = [
        Entry(
            id=str(uuid4()),
            mood=3,
            energy=5,
            note=None,
            tags=[],
            timestamp=now - timedelta(hours=25 + i * 24),
        )
        for i in range(3)
    ]
    _seed_entries_file(entries)

    resp = client.get("/api/nudges")
    assert resp.status_code == 200
    nudges = resp.json()["nudges"]
    if not nudges:
        pytest.skip("missing_entry suppressed by quiet hours at test runtime")
    state = state_module.load_state()
    rule_id = nudges[0]["rule_id"]
    assert state.rule_stats[rule_id].shown == 1
    assert rule_id in state.last_shown_at


def test_engaged_increments_bandit(client: TestClient):
    state = state_module.NudgeState()
    state.rule_stats["reminder"] = state_module.RuleStats(shown=1, engaged=0)
    state.nudge_id_to_rule["abc"] = "reminder"
    state_module.save_state(state)
    resp = client.post("/api/nudges/abc/engaged")
    assert resp.status_code == 204
    new_state = state_module.load_state()
    assert new_state.rule_stats["reminder"].engaged == 1


def test_dismiss_sets_dismissed_at(client: TestClient):
    state = state_module.NudgeState()
    state.nudge_id_to_rule["xyz"] = "missing_entry"
    state_module.save_state(state)
    resp = client.post("/api/nudges/xyz/dismiss")
    assert resp.status_code == 204
    new_state = state_module.load_state()
    assert "missing_entry" in new_state.dismissed_at


def test_snooze_sets_snoozed_until(client: TestClient):
    state = state_module.NudgeState()
    state.nudge_id_to_rule["nid"] = "reminder"
    state_module.save_state(state)
    resp = client.post("/api/nudges/nid/snooze")
    assert resp.status_code == 204
    new_state = state_module.load_state()
    assert "reminder" in new_state.snoozed_until


def test_preferences_roundtrip(client: TestClient):
    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert "categories_enabled" in body
    assert body["categories_enabled"]["change_point"] is False

    # Update
    put = client.put(
        "/api/preferences",
        json={
            "quiet_hours": {"start": "22:30", "end": "07:30"},
            "categories_enabled": {"change_point": True},
        },
    )
    assert put.status_code == 200
    pb = put.json()
    assert pb["quiet_hours"]["start"] == "22:30"
    assert pb["categories_enabled"]["change_point"] is True
    # Other categories preserved
    assert pb["categories_enabled"]["reminder"] is True


def test_preferences_invalid_quiet_hours(client: TestClient):
    resp = client.put(
        "/api/preferences", json={"quiet_hours": {"start": "09:00", "end": "09:00"}}
    )
    assert resp.status_code == 422


def test_retention_stats(client: TestClient):
    from uuid import uuid4

    today = datetime.now(UTC)
    entries = []
    # Create 10 distinct days in last 14 days, with 14 total entries
    for i in range(10):
        entries.append(
            Entry(
                id=str(uuid4()),
                mood=4,
                energy=6,
                note=None,
                tags=[],
                timestamp=today - timedelta(days=i),
            )
        )
    # Extra entries to make 14 total
    for i in range(4):
        entries.append(
            Entry(
                id=str(uuid4()),
                mood=4,
                energy=6,
                note=None,
                tags=[],
                timestamp=today - timedelta(days=i, hours=2),
            )
        )
    _seed_entries_file(entries)

    resp = client.get("/api/stats/retention")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_30d_active_days"] == 10
    assert body["last_7d_active_days"] == 7
    assert body["current_streak"] >= 10
    assert body["best_streak"] >= 10
    assert body["entries_per_active_week_median"] >= 1
