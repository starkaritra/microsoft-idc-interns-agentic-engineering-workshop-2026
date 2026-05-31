"""Nudges HTTP routes."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, HTTPException

from ..nudges.engine import compute_nudges
from ..nudges.preferences import load_prefs
from ..nudges.state import NudgeState, RuleStats, load_state, save_state
from ..storage import list_entries


router = APIRouter()


@router.get("/nudges")
def get_nudges():
    """Compute current nudges and mark any returned ones as shown."""
    entries = list_entries()
    state = load_state()
    prefs = load_prefs()
    now = datetime.now(timezone.utc)
    nudges = compute_nudges(entries, state, prefs, now)

    if nudges:
        for n in nudges:
            stats = state.rule_stats.get(n.rule_id, RuleStats())
            stats.shown += 1
            state.rule_stats[n.rule_id] = stats
            state.last_shown_at[n.rule_id] = n.emitted_at
            state.nudge_id_to_rule[n.id] = n.rule_id
            if n.rule_id == "first_insight" and n.rule_id not in state.one_shot_fired:
                state.one_shot_fired.append(n.rule_id)
        save_state(state)

    return {"nudges": [n.model_dump(mode="json") for n in nudges]}


def _rule_from_id(state: NudgeState, ident: str) -> str:
    """Resolve a request identifier to a rule_id.

    Accepts either a nudge emission id (UUID) or a rule_id string.
    """
    if ident in state.nudge_id_to_rule:
        return state.nudge_id_to_rule[ident]
    return ident


@router.post("/nudges/{ident}/engaged", status_code=204)
def mark_engaged(ident: str):
    state = load_state()
    rule_id = _rule_from_id(state, ident)
    stats = state.rule_stats.get(rule_id, RuleStats())
    stats.engaged += 1
    state.rule_stats[rule_id] = stats
    save_state(state)


@router.post("/nudges/{ident}/dismiss", status_code=204)
def dismiss(ident: str):
    state = load_state()
    rule_id = _rule_from_id(state, ident)
    state.dismissed_at[rule_id] = datetime.now(timezone.utc)
    save_state(state)


@router.post("/nudges/{ident}/snooze", status_code=204)
def snooze(ident: str):
    state = load_state()
    rule_id = _rule_from_id(state, ident)
    now = datetime.now(timezone.utc)
    # Snooze until next 09:00 local (treated as UTC here for single-user simplicity)
    target = datetime.combine(now.date(), time(9, 0), tzinfo=timezone.utc)
    if target <= now:
        target = target + timedelta(days=1)
    state.snoozed_until[rule_id] = target
    save_state(state)
