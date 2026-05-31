# Smart Nudges — PRD & Integration Contract

**Status:** Draft v1 · **Owner:** Pulse Eng · **Brief:** `briefs/03-smart-nudges.md`

This document is the single source of truth for the Smart Nudges feature. The backend and frontend handoff docs derive their contracts from here. If something disagrees, this file wins.

---

## Problem Statement

Pulse loses ~70% of users between Day 3 and Day 7. The product hypothesis is that users churn before the app delivers any insight — logging feels like a chore with no payoff. We need a system that (a) brings users back at the right moment, (b) gives them something *back* when they return, and (c) never feels coercive or guilt-inducing.

A hard constraint: this codebase is a **single-user, JSON-backed, no-auth, no-scheduler** app. Most of the brief's strategy (segmentation, push channels, A/B testing) is not implementable here and is explicitly cut. We deliver an **in-app nudge engine**, computed on demand, with honest single-user retention metrics.

## Solution

A `Nudge Engine` that, on every dashboard load, returns 0–3 ranked nudge cards. Nudges are produced by composable `NudgeRule`s, ranked by a Thompson-sampled bandit with time-decay, gated by user preferences and a skip-predictor that suppresses nudges when the user is likely to log anyway. The user controls categories, quiet hours, and reminder time from a `/settings` page.

Four algorithms power v1:
1. **Deterministic rules engine** — base layer.
2. **von Mises KDE on entry hours** — personalizes the daily reminder time.
3. **Logistic skip-predictor** — suppresses redundant reminders.
4. **CUSUM change-point detection** — fires *reflection* nudges on sustained mood/energy shifts.
5. **Thompson sampling + Hawkes-style time decay** — picks which nudge to show when multiple fire.

## User Stories

1. As a returning user, I want to see at most one nudge on the dashboard, so that the app never feels like spam.
2. As a new user (< 3 entries), I want no nudges at all, so that onboarding is friction-free.
3. As a daily logger, I want my reminder to fire close to when I usually log, so that it feels timely rather than arbitrary.
4. As a user who already logged today, I want the system to *not* nudge me to log again, so that nudges remain meaningful.
5. As a user, I want to see a celebratory message when I hit 3, 7, or 30 entries, so that progress feels rewarding.
6. As a user reaching my 7th entry, I want a one-time "first insight" card showing a real pattern from my data, so that I see the payoff Priya promised.
7. As a user whose mood has dipped for several days, I want a gentle reflection prompt — not a diagnosis — so that I can choose to engage on my own terms.
8. As a user, I want to see when a behavior (e.g. `exercise`) correlates with better mood, so that the app gives me something I couldn't easily compute myself.
9. As a user, I want to dismiss any nudge in one tap, so that I can stay in control.
10. As a user, I want to snooze a nudge for the day, so that I can defer without disabling.
11. As a user, I want to turn off any nudge category, so that I can opt out without uninstalling.
12. As a user, I want to set quiet hours, so that no nudge is shown overnight.
13. As a user, I want to set my preferred reminder time as an override, so that I can ignore the personalized algorithm.
14. As a user, I want to see honest local retention stats (last 7 / 30 days), so that I can judge my own consistency.
15. As an engineer, I want every rule to be a pure function of `(entries, state, prefs, now)`, so that the engine is fully testable without time mocking gymnastics.
16. As an engineer, I want the bandit and skip-predictor to be deterministic given a seed, so that tests are reproducible.

## Implementation Decisions

### Architecture

- A new package `app/nudges/` contains: `rules/` (one file per rule), `algorithms/` (von Mises, skip-predictor, CUSUM, Thompson), `engine.py` (composition), `state.py` (NudgeState I/O), `preferences.py` (Preferences I/O).
- The engine entry point is a pure function: `compute_nudges(entries, state, prefs, now) -> list[Nudge]`. Side effects (state writes) happen at the route layer only.
- Each `NudgeRule` exposes `evaluate(ctx) -> Nudge | None`. Rules never mutate state.
- The bandit selects among candidate nudges; never invents them.
- Algorithms live behind narrow interfaces (deep modules). The route layer never imports numpy/sklearn — only `engine.py` does.

### Storage

- `.data/nudge_state.json` — `{ rule_stats: {rule_id: {shown, engaged}}, last_shown_at: {rule_id: iso}, dismissed_at: {nudge_id: iso}, snoozed_until: {rule_id: iso}, one_shot_fired: [rule_id] }`.
- `.data/preferences.json` — `{ quiet_hours: {start: "21:00", end: "09:00"}, reminder_time_override: null | "HH:MM", categories_enabled: {reminder: true, missing_entry: true, first_insight: true, streak: true, pattern: true, change_point: false} }`.
- File I/O follows the existing `storage.py` pattern (read-all / write-all). No locking; single-user assumption.

### Engagement signal (decided)

A nudge is **engaged** if the user creates an entry within **30 minutes** of the nudge being marked `shown`. Logged decision; see "Known design tensions" below — this signal conflates organic logging with nudge-driven logging.

### Defaults (decided)

| Category | Default | Notes |
|---|---|---|
| `reminder` | ON | von Mises timing, falls back to 09:00 with < 7 entries |
| `missing_entry` | ON | Only fires if total entries ≥ 3 |
| `first_insight` | ON | One-shot at entry #7 |
| `streak` | ON | Celebration only; never loss-framing |
| `pattern` | ON | Requires ≥ 10 tagged days per tag + permutation p < 0.05 |
| `change_point` | OFF | Opt-in only; copy must be reviewed |

Quiet hours default: **21:00 – 09:00 local**.

### Algorithms (deep modules, ~50 lines each)

- `von_mises_timing.compute_optimal_reminder(entry_hours: list[int], fallback: time) -> time` — fits von Mises on hour-of-day circle, returns mode clamped to non-quiet hours. Requires ≥ 7 entries.
- `skip_predictor.probability_of_no_entry_today(features) -> float` — sklearn `LogisticRegression` retrained on demand from user history; features `[hours_since_last, dow, entries_last_7d, nudge_was_shown]`. Requires ≥ 30 days of data, else returns 0.5.
- `change_point.detect_recent_shift(series: list[float], window: int = 5) -> Shift | None` — CUSUM with effect threshold 0.8 (mood) / 1.5 (energy), min sustained length 5.
- `bandit.select(candidates, state, now, decay_tau) -> Nudge` — Thompson sample from `Beta(engaged+α, shown-engaged+β)` per rule, multiplied by `exp(-Δt / τ_category)`. Deterministic when `random.Random(seed)` is passed.

### API contract

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/nudges` | Returns `{nudges: Nudge[]}` (0–3, ranked). **Side effect:** marks returned nudges as `shown` in state. |
| `POST` | `/api/nudges/{nudge_id}/engaged` | Called by frontend when user creates an entry within 30 min of seeing nudge. Updates bandit. |
| `POST` | `/api/nudges/{rule_id}/dismiss` | Records dismissal. |
| `POST` | `/api/nudges/{rule_id}/snooze` | Snoozes that rule until next morning. |
| `GET` | `/api/preferences` | Returns full Preferences object. |
| `PUT` | `/api/preferences` | Replaces Preferences. |
| `GET` | `/api/stats/retention` | Returns `{last_7d_active_days, last_30d_active_days, current_streak, best_streak, entries_per_active_week_median}`. |

### `Nudge` shape

```ts
{
  id: string;            // UUID per emission
  rule_id: string;       // stable: "reminder" | "missing_entry" | ...
  category: string;      // same set as preferences.categories_enabled
  title: string;
  body: string;
  cta?: { label: string; route: string };
  priority: number;      // 0..1, post-bandit score
  emitted_at: string;    // ISO
}
```

### Copy rules (binding)

- Never use loss framing. "You broke your streak" → "New streak started today."
- Reflection nudges (change-point) phrase as questions, never diagnoses. "Noticed a shift this week — want to note what changed?" not "Your mood seems low."
- Reminder copy never references missed days unless `missing_entry` rule fires.

## Testing Decisions

Tests verify **observable behavior through public interfaces**: HTTP responses, file contents after route calls, and the public output of `compute_nudges`. We do not test private helpers, algorithm internals, or numpy/sklearn correctness (those have their own tests).

Modules under test:
- `compute_nudges` — given fixtures of `(entries, state, prefs, now)`, asserts which nudge rule IDs appear and their order.
- Each rule's `evaluate` — boundary cases (just-below / just-above firing thresholds).
- `bandit.select` — with seeded RNG, asserts cold-start behavior, decay suppression, and convergence to higher-engagement arm after N synthetic trials.
- `change_point.detect_recent_shift` — known synthetic series with planted shift; asserts detection + no false positives on flat noise.
- `von_mises_timing.compute_optimal_reminder` — known cluster of hours returns hour ± 1; fewer than 7 entries returns fallback.
- Routes — full HTTP round-trip, assert state file contents after `POST /engaged`, `/dismiss`, `/snooze`.

Prior art: `backend/tests/test_entries.py` and `test_stats.py` use FastAPI `TestClient` with a temp `.data/` dir. Same pattern applies.

**TDD discipline:** vertical tracer-bullet slices, one rule at a time. No horizontal "all tests first." See `backend_handoff.md` for the ordered test list.

## Known design tensions (logged honestly)

1. **Engagement signal = "entry within 30 min"** conflates organic logging with nudge-driven logging. The bandit may over-credit reminders that fire near typical logging time. Mitigation: include `nudge_was_shown` as a feature in the skip-predictor so we can disentangle later. Revisit after 30 days of data.
2. **Pattern nudges ON by default** despite recommendation to gate behind opt-in. Risk: a noisy pattern card on day 8 erodes trust. Mitigation: hard permutation-test gate (p < 0.05, |Δ| ≥ 0.5, n ≥ 10 tagged days).
3. **Change-point OFF by default** is the right call — the wellness-app dystopia failure mode is real here.
4. **Bandit cold-start** uses informed priors (pessimistic for `missing_entry`, optimistic for `first_insight`). Documented in `bandit.py`.
5. **Skip-predictor is self-fulfilling** — the nudge changes the label. Mitigated by `nudge_was_shown` feature; not solved.

## Out of Scope

- Multi-user segmentation, cohort analytics, A/B testing infrastructure.
- Push notifications, email, SMS — any out-of-process channel.
- Background schedulers / cron / Celery. All computation is on-demand.
- ML-driven nudge copy generation (LLMs). All copy is templated.
- Cross-device sync. Single user, single device.
- Advocacy / referral mechanics from the brief's Stage 4.

## Further Notes

- New backend deps: `numpy`, `scikit-learn`. Added to `backend/requirements.txt`.
- The retention metrics endpoint (`/api/stats/retention`) is the *honest* answer to Priya's D1/D3/D7 numbers — it measures one user, locally. Anything more requires infra not in scope.
- Workshop framing: the rules engine is the deep module; the algorithms are pluggable. A future contributor can add a new rule in ~20 lines without touching engine internals.
