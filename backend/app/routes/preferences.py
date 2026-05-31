"""Preferences HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from ..nudges.preferences import Preferences, load_prefs, save_prefs


router = APIRouter()


@router.get("/preferences", response_model=Preferences)
def get_preferences():
    return load_prefs()


@router.put("/preferences", response_model=Preferences)
def put_preferences(body: dict):
    """Merge body into existing prefs and persist."""
    current = load_prefs().model_dump(mode="json")
    # Shallow merge with nested merge for quiet_hours and categories_enabled
    merged = dict(current)
    for k, v in body.items():
        if k in ("quiet_hours", "categories_enabled") and isinstance(v, dict) and isinstance(current.get(k), dict):
            sub = dict(current[k])
            sub.update(v)
            merged[k] = sub
        else:
            merged[k] = v
    try:
        prefs = Preferences(**merged)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False, include_context=False, include_input=False))
    save_prefs(prefs)
    return prefs
