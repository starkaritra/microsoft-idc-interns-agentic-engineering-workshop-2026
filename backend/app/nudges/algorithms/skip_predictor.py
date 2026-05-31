"""Logistic skip-predictor: P(no entry today)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable


def probability_of_no_entry_today(history: list, now: datetime) -> float:
    """Return P(user does NOT log today) given entry history.

    Returns 0.5 when insufficient data (< 30 distinct days).
    Trains a tiny logistic regression on-the-fly:
      features per (past day): [hours_since_last_before_day, dow, entries_last_7d]
      label: 1 if no entry that day, else 0.
    Then predicts for `now`.
    """
    if not history or len(history) < 5:
        return 0.5

    # Build per-day records over the past 60 days ending yesterday
    timestamps = sorted(
        getattr(e, "timestamp", None) or e["timestamp"] for e in history
    )
    if not timestamps:
        return 0.5

    # Distinct days
    days = sorted({ts.date() for ts in timestamps})
    if len(days) < 30:
        return 0.5

    import numpy as np
    from sklearn.linear_model import LogisticRegression

    today = now.date()
    start = today - timedelta(days=60)

    by_day: dict = {}
    for ts in timestamps:
        by_day.setdefault(ts.date(), []).append(ts)

    rows = []
    labels = []
    last_ts: datetime | None = None
    for i in range(60):
        day = start + timedelta(days=i)
        has = day in by_day
        # hours since last entry, capped
        if last_ts is None:
            hours_since = 168.0
        else:
            hours_since = min(168.0, (datetime.combine(day, datetime.min.time(), tzinfo=last_ts.tzinfo) - last_ts).total_seconds() / 3600.0)
            if hours_since < 0:
                hours_since = 0.0
        dow = day.weekday()
        # entries in prior 7 days
        prior = sum(
            len(by_day.get(day - timedelta(days=k), [])) for k in range(1, 8)
        )
        rows.append([hours_since, dow, prior])
        labels.append(0 if has else 1)
        if has:
            last_ts = max(by_day[day])

    X = np.array(rows, dtype=float)
    y = np.array(labels, dtype=int)
    if len(set(y)) < 2:
        return 0.5

    model = LogisticRegression(max_iter=200)
    model.fit(X, y)

    # Build feature for today
    if last_ts is None:
        hours_since_now = 168.0
    else:
        hours_since_now = min(
            168.0, (now - last_ts).total_seconds() / 3600.0
        )
    dow_now = today.weekday()
    prior_now = sum(
        len(by_day.get(today - timedelta(days=k), [])) for k in range(1, 8)
    )
    proba = float(model.predict_proba([[hours_since_now, dow_now, prior_now]])[0, 1])
    return proba
