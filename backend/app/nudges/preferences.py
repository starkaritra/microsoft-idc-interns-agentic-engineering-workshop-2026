"""Preferences persistence — JSON file, atomic write."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .. import storage


PREFS_FILENAME = "preferences.json"


class QuietHours(BaseModel):
    start: str = "21:00"
    end: str = "09:00"

    @field_validator("start", "end")
    @classmethod
    def _valid_hhmm(cls, v: str) -> str:
        try:
            time.fromisoformat(v)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid HH:MM: {v}") from exc
        return v

    @model_validator(mode="after")
    def _start_neq_end(self) -> "QuietHours":
        if self.start == self.end:
            raise ValueError("quiet hours start must differ from end")
        return self


DEFAULT_CATEGORIES = {
    "reminder": True,
    "missing_entry": True,
    "first_insight": True,
    "streak": True,
    "pattern": True,
    "change_point": False,
}


class Preferences(BaseModel):
    quiet_hours: QuietHours = Field(default_factory=QuietHours)
    reminder_time_override: Optional[str] = None
    categories_enabled: dict[str, bool] = Field(default_factory=lambda: dict(DEFAULT_CATEGORIES))

    @field_validator("reminder_time_override")
    @classmethod
    def _valid_override(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            time.fromisoformat(v)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid HH:MM: {v}") from exc
        return v

    @model_validator(mode="after")
    def _fill_defaults(self) -> "Preferences":
        merged = dict(DEFAULT_CATEGORIES)
        merged.update(self.categories_enabled or {})
        self.categories_enabled = merged
        return self


def _prefs_path() -> Path:
    return storage.DATA_DIR / PREFS_FILENAME


def load_prefs() -> Preferences:
    storage._ensure_data_dir()
    path = _prefs_path()
    if not path.exists():
        return Preferences()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Preferences()
    return Preferences(**raw)


def save_prefs(prefs: Preferences) -> None:
    storage._ensure_data_dir()
    path = _prefs_path()
    payload = prefs.model_dump(mode="json")
    fd, tmp = tempfile.mkstemp(prefix=".preferences.", suffix=".tmp", dir=str(path.parent))
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
