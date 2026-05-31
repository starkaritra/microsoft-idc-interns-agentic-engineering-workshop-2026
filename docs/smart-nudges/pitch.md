# Pulse — Smart Nudges
### Product Pitch · 5-slide deck

---

## Slide 1 — The Problem

**Pulse loses 7 of every 10 users between Day 3 and Day 7.**

| Cohort | Retention |
|---|---|
| Day 1 → Day 3 | 72% |
| Day 3 → Day 7 | 31% |
| Day 7 → Day 30 | 14% |

Users churn before the app delivers any insight. Logging feels like a chore with no payoff.

**The trap:** the obvious fix — "send more reminders" — is also the fastest way to get uninstalled. We need a system that *earns* attention instead of demanding it.

---

## Slide 2 — The Solution: A Nudge Engine That Earns Its Welcome

A composable, on-demand nudge system with **five behavioral rules** and **four lightweight algorithms**, all running locally on the user's own data. No LLMs. No spam. No streak-shaming.

**Five nudge categories:**
1. **Reminder** — daily check-in, timed to *your* logging habits
2. **Missing-entry** — gentle prompt after 24h, only post-onboarding
3. **First-insight** — one-shot celebration at entry #7, reveals a real pattern
4. **Streak milestones** — celebration-only at 3 / 7 / 30 days (never loss-framed)
5. **Pattern nudges** — statistically validated correlations (e.g. *"You score +0.8 mood on `exercise` days, p<0.05"*)

Plus: **change-point reflection** (opt-in) — fires only when CUSUM detects a real sustained shift in your mood/energy.

**Hard constraints, by design:**
- ≤ 1 nudge visible at a time, ever.
- No nudges before entry #3 (onboarding shield).
- One-tap dismiss · one-tap snooze · one-tap *disable everything*.
- Quiet hours respected (default 21:00 – 09:00).
- Zero loss-framing copy. Banned words enforced in tests.

---

## Slide 3 — The Algorithms (and Why They Matter)

The differentiator isn't *that* we nudge — it's *when*, *which*, and *whether at all*.

| Algorithm | What it does | Why it's there |
|---|---|---|
| **von Mises KDE** on entry hours | Learns your circadian logging mode (handles 23→0 wrap-around) | Reminder fires near *your* time, not a hardcoded 9am |
| **Logistic skip-predictor** | Predicts P(no entry today) from `[hours_since_last, dow, entries_last_7d, nudge_was_shown]` | Suppresses reminders when you'd log anyway → kills the #1 spam vector |
| **CUSUM change-point** | Detects sustained mood/energy shifts (5-day window, magnitude threshold) | Powers *event-driven* reflection, not calendar-driven nagging |
| **Thompson sampling + Hawkes decay** | `Beta(engaged+α, shown-engaged+β) × exp(-Δt/τ)` per rule | Self-tunes which nudges *you* find valuable, no A/B infra needed |
| **Permutation test (1000 shuffles)** | Gates pattern nudges on p<0.05 + |Δ|≥0.5 + n≥10 tagged days | Eliminates spurious "you're happier on Tuesdays" garbage |

All five fit in **<300 lines of NumPy + scikit-learn**. Cold-start handled by informed Beta priors. Reproducible under seed.

---

## Slide 4 — What's Shipping

**Backend (FastAPI + JSON storage)**
- `app/nudges/` — engine, state, preferences, 6 rules, 4 algorithms
- New endpoints: `GET /api/nudges`, `POST /api/nudges/{id}/{engaged,dismiss,snooze}`, `GET|PUT /api/preferences`, `GET /api/stats/retention`
- Single-user **honest retention metrics** — last-7d / last-30d active days, current streak, best streak, median entries-per-active-week (the only retention numbers we can defend in this codebase)

**Frontend (React + Vite + TS + Tailwind)**
- `<NudgeStack />` — caps at 1, fail-soft (broken nudge feature can't break the dashboard)
- `<NudgeCard />` — title · body · CTA · dismiss · snooze
- `/settings` page — quiet hours, reminder override, per-category toggles, **"disable all" trust escape hatch**
- `<RetentionPanel />` on dashboard — your real numbers, locally computed
- `nudgeTracking.ts` — sessionStorage-based 30-min engagement attribution

**Test discipline**
- TDD vertical tracer-bullet slices (18 backend + 13 frontend), one test → one impl → repeat
- Banned-word assertions enforce copy rules in CI
- Algorithms tested with seeded RNGs; routes tested via real HTTP round-trips with temp `.data/` dirs

---

## Slide 5 — What We Cut, and What We Refuse to Pretend

**Cut, with reasoning:**
- ❌ Push / email / SMS — no infra, not pretending we have it
- ❌ Multi-user segmentation, A/B framework, holdout cohorts — n=1, all of this is theater
- ❌ Background schedulers — engine is on-demand, no Celery/cron
- ❌ LLM-generated copy — every string is reviewed, templated, tested
- ❌ Advocacy / referral mechanics — out of scope until retention proves itself

**Logged tensions (we documented these instead of hiding them):**
1. Engagement signal = "entry within 30 min of nudge" conflates organic vs. nudge-driven logging. Mitigation: `nudge_was_shown` is a feature in the skip-predictor. Revisit at 30 days of data.
2. Pattern nudges are ON by default despite cold-start risk. Mitigation: hard permutation gate.
3. Skip-predictor is self-fulfilling. Acknowledged, not solved.

**The principle:**
> Nudges that respect the user are nudges the user keeps on.
> Every default, threshold, and copy rule in this build optimizes for *not getting turned off* — because a nudge engine the user disabled is worth zero, regardless of how clever its math is.
