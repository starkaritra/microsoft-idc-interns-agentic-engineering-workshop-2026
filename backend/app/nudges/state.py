"""NudgeState persistence — JSON file, atomic write."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .. import storage


STATE_FILENAME = "nudge_state.json"


class RuleStats(BaseModel):
    shown: int = 0
    engaged: int = 0


class NudgeState(BaseModel):
    rule_stats: dict[str, RuleStats] = Field(default_factory=dict)
    last_shown_at: dict[str, datetime] = Field(default_factory=dict)
    dismissed_at: dict[str, datetime] = Field(default_factory=dict)
    snoozed_until: dict[str, datetime] = Field(default_factory=dict)
    one_shot_fired: list[str] = Field(default_factory=list)
    # Map nudge emission id -> rule_id, so /engaged + /dismiss by id can resolve.
    nudge_id_to_rule: dict[str, str] = Field(default_factory=dict)


def _state_path() -> Path:
    return storage.DATA_DIR / STATE_FILENAME


def load_state() -> NudgeState:
    storage._ensure_data_dir()
    path = _state_path()
    if not path.exists():
        return NudgeState()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return NudgeState()
    return NudgeState(**raw)


def save_state(state: NudgeState) -> None:
    storage._ensure_data_dir()
    path = _state_path()
    payload = state.model_dump(mode="json")
    # Atomic write: temp file + rename
    fd, tmp = tempfile.mkstemp(prefix=".nudge_state.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
