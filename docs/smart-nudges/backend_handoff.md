# Backend Handoff — Smart Nudges

**Reads from:** `integration.md` (contract). **Owner:** backend.
**Stack:** FastAPI · Pydantic · file-based JSON · pytest. Adds: `numpy`, `scikit-learn`.

This doc describes *what* to build and *in what order*, using TDD tracer-bullet slices. Each slice is one RED → GREEN cycle. Do not write all tests up front.

---

## Module map (deep modules)

```
backend/app/
  nudges/
    __init__.py
    engine.py            # compute_nudges(entries, state, prefs, now) -> list[Nudge]
    state.py             # load_state() / save_state(); NudgeState model
    preferences.py       # load_prefs() / save_prefs(); Preferences model
    models.py            # Nudge, NudgeContext, RuleStats
    rules/
      __init__.py        # ALL_RULES registry
      base.py            # NudgeRule protocol
      reminder.py
      missing_entry.py
      first_insight.py
      streak.py
      pattern.py
      change_point_reflection.py
    algorithms/
      __init__.py
      von_mises_timing.py
      skip_predictor.py
      change_point.py
      bandit.py
  routes/
    nudges.py            # /api/nudges, /engaged, /dismiss, /snooze
    preferences.py       # /api/preferences
    stats.py             # + /api/stats/retention
```

**Public interfaces (the only things tests touch):**
- `engine.compute_nudges(entries, state, prefs, now, rng) -> list[Nudge]`
- Each `rules/*.py` exports a `RULE` instance with `.id`, `.category`, `.evaluate(ctx) -> Nudge | None`.
- `algorithms.bandit.select(candidates, state, now, rng) -> Nudge`
- `algorithms.von_mises_timing.compute_optimal_reminder(hours, fallback) -> time`
- `algorithms.change_point.detect_recent_shift(series, window) -> Shift | None`
- `algorithms.skip_predictor.probability_of_no_entry_today(history, now) -> float`
- HTTP endpoints listed in `integration.md`.

Everything else is private and may change freely.

---

## Files to add / modify

**Add:** all files under `backend/app/nudges/`, `backend/app/routes/nudges.py`, `backend/app/routes/preferences.py`, plus tests under `backend/tests/nudges/` and `backend/tests/test_routes_nudges.py`, `test_routes_preferences.py`, `test_routes_retention.py`.

**Modify:**
- `backend/app/main.py` — register `nudges.router` and `preferences.router`.
- `backend/app/routes/stats.py` — add `GET /stats/retention`.
- `backend/requirements.txt` — add `numpy>=1.26`, `scikit-learn>=1.4`.
- `backend/seed.py` — extend so retention/insight rules have data to operate on (no schema change needed).

**Do not modify:** `models/entry.py`, `storage.py` (entries), existing entry routes. The feature is strictly additive.

---

## TDD tracer-bullet plan (ordered)

Each slice = one test, then minimal code to pass. Do not skip ahead.

### Slice 1 — Engine returns empty list for new user
- **Test:** `compute_nudges([], empty_state, default_prefs, now) == []`.
- **Code:** Create `engine.py`, `models.py`, `state.py`, `preferences.py` stubs. `compute_nudges` returns `[]`.

### Slice 2 — Reminder rule fires at user's typical logging time
- **Test:** Given 10 entries all logged at hour 8, calling engine at 08:00 returns one nudge with `rule_id == "reminder"`; at 14:00 returns `[]`.
- **Code:** Implement `von_mises_timing.compute_optimal_reminder` (numpy, von Mises KDE on circle). Implement `rules/reminder.py`. Wire into engine.

### Slice 3 — Reminder respects quiet hours
- **Test:** Same fixture, prefs with quiet hours 07:00–10:00, engine at 08:00 returns `[]`.
- **Code:** Add quiet-hours check in engine before evaluating rules.

### Slice 4 — No nudges before entry #3 (onboarding shield)
- **Test:** 2 entries today, all other conditions met, engine returns `[]`.
- **Code:** Onboarding gate in engine.

### Slice 5 — Missing-entry rule after 24h
- **Test:** Last entry 25h ago, ≥3 total entries, engine emits `missing_entry` nudge.
- **Code:** `rules/missing_entry.py`.

### Slice 6 — Streak milestone celebration (no loss framing)
- **Test:** 7 consecutive days of entries → `streak` nudge with title containing "7"; 1 missed day → no negative-framed nudge fires (assert no nudge with words from a banned list: "broke", "lost", "missed").
- **Code:** `rules/streak.py`. Implement streak computation from entries.

### Slice 7 — First-insight one-shot at entry #7
- **Test:** Exactly 7 entries, state has empty `one_shot_fired` → `first_insight` nudge emitted; second call with state now containing `"first_insight"` → not emitted.
- **Code:** `rules/first_insight.py`. Engine writes `one_shot_fired` on emission (in route layer, not engine — test via route in Slice 13).

### Slice 8 — CUSUM detects planted shift
- **Test:** Synthetic series `[4]*10 + [2]*7` → `detect_recent_shift` returns `Shift(direction="down", magnitude≈2)`; flat `[3]*20` returns `None`.
- **Code:** `algorithms/change_point.py`.

### Slice 9 — Change-point rule emits only when category enabled
- **Test:** Planted-shift fixture + prefs with `change_point: False` → no nudge. With `True` → nudge with curious copy (no banned diagnostic words: "depressed", "low mood", "concerning").
- **Code:** `rules/change_point_reflection.py`.

### Slice 10 — Pattern rule gated by permutation test
- **Test:** Tag `exercise` present on 12 days, mood +1.0 on those days → pattern nudge. Same delta but only 4 tagged days → no nudge. Random tag assignment (planted null) → no nudge across 100 seeds with FPR ≤ 0.07.
- **Code:** `rules/pattern.py` with inline permutation test (numpy, 1000 shuffles).

### Slice 11 — Skip-predictor suppresses likely-to-log users
- **Test:** History where user logged every day at 09:00 for 40 days, current time 08:55 → reminder is suppressed (predictor returns low P(no entry)). At 08:00 day 1 with no history, suppression off (returns 0.5, threshold not crossed).
- **Code:** `algorithms/skip_predictor.py` using `sklearn.linear_model.LogisticRegression`. Engine wires it as a pre-filter on `reminder` only.

### Slice 12 — Bandit picks higher-engagement arm with seeded RNG
- **Test:** With seeded `random.Random(42)`, two candidate nudges where rule A has `(shown=20, engaged=15)` and rule B has `(shown=20, engaged=2)`, `bandit.select` returns A in ≥ 90 / 100 calls. Cold-start (`shown=0`) for both → distribution within ±15% of 50/50 over 200 calls.
- **Code:** `algorithms/bandit.py` (Thompson + time decay via `exp(-Δt/τ)`).

### Slice 13 — `GET /api/nudges` marks emissions as `shown` in state
- **Test:** Empty state → call endpoint → state file contains `rule_stats[<rule>].shown == 1` and `last_shown_at[<rule>]` set.
- **Code:** `routes/nudges.py`. Route is the only place that mutates state.

### Slice 14 — `POST /api/nudges/{id}/engaged` updates bandit
- **Test:** After GET emits nudge with id X, POST `/engaged` increments `engaged` count for that rule.
- **Code:** Engaged route.

### Slice 15 — Dismiss + snooze
- **Test:** `POST /dismiss` sets `dismissed_at`; subsequent `GET /api/nudges` within decay window suppresses that rule. `POST /snooze` sets `snoozed_until` to next 09:00 local; GET before that time does not return the rule.
- **Code:** Dismiss + snooze routes; engine respects both.

### Slice 16 — Preferences round-trip
- **Test:** `PUT /api/preferences` with partial changes → `GET` returns merged result; invalid quiet hours (`start == end`) → 422.
- **Code:** `routes/preferences.py`.

### Slice 17 — Retention stats endpoint
- **Test:** Given 14 entries over 10 distinct days in the last 30 → `last_30d_active_days == 10`, `entries_per_active_week_median` correct, `current_streak` computed from consecutive days ending today.
- **Code:** Extend `routes/stats.py`.

### Slice 18 — Engine cap: never returns > 1 nudge
- **Test:** Construct a context where all rules fire → exactly 1 nudge in response.
- **Code:** Final cap in engine after bandit selection.

---

## Test conventions

- Use `pytest` + FastAPI `TestClient` (existing pattern in `tests/conftest.py`).
- Extend `conftest.py` with fixtures: `temp_data_dir`, `seed_entries(hours_pattern)`, `default_prefs`, `seeded_rng`.
- All time-dependent tests pass an explicit `now: datetime` — never call `datetime.now()` in the engine.
- Algorithm tests use `numpy.random.default_rng(SEED)` for reproducibility.
- Mocking: **do not** mock `numpy`, `sklearn`, or filesystem. Use real temp dirs (see `mocking.md` in skills). The only legitimate mock is `now`.

## Non-goals for this handoff

- No middleware for usage tracking yet — retention stats are derived from entries alone.
- No streaming / SSE. Frontend polls on dashboard load.
- No migration script for existing `.data/`; absent `nudge_state.json` / `preferences.json` are auto-created on first read.

## Risks for backend specifically

- **sklearn cold imports are slow (~300ms).** Import lazily inside `skip_predictor.probability_of_no_entry_today` so test startup stays fast.
- **numpy von Mises fit on < 5 hours** can be numerically unstable. Hard-gate on `len(entry_hours) >= 7`; fall back to `prefs.reminder_time_override or time(9, 0)`.
- **JSON write race** in the single-user case is not a concern, but a concurrent GET during an in-flight POST could read partial state. Use the existing `_write_all` pattern (write to temp, rename) — verify `storage.py` does atomic rename; if not, add it.
