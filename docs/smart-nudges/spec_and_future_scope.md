# Smart Nudges — Specs & Future Scope Report

**Status:** v1 shipped · **Owner:** Pulse Eng · **Doc set:** `integration.md`, `backend_handoff.md`, `frontend_handoff.md`, `pitch.md`, `demo.md`.

---

## Current Specifications

### System overview
On-demand, single-user, in-app nudge engine. Computes ≤ 1 nudge per dashboard load from local JSON data. No background workers, no LLMs, no out-of-process channels.

### Stack additions (over base Pulse)
| Layer | Added |
|---|---|
| Backend deps | `numpy >= 1.26`, `scikit-learn >= 1.4` |
| Backend modules | `app/nudges/{engine,state,preferences,models,rules/*,algorithms/*}`, `app/routes/{nudges,preferences}.py`, `routes/stats.py` (+ retention) |
| Frontend modules | `components/{NudgeStack,NudgeCard,PreferencesForm,RetentionPanel}.tsx`, `pages/Settings.tsx`, `lib/nudgeTracking.ts` |
| Storage | `.data/nudge_state.json`, `.data/preferences.json` (auto-created) |

### Nudge rules
| Rule | Default | Gate |
|---|---|---|
| `reminder` | ON | von Mises hour mode (≥7 entries) + skip-predictor (P(no entry today) ≥ 0.4) |
| `missing_entry` | ON | ≥ 3 total entries · last entry > 24h ago |
| `first_insight` | ON | One-shot at entry #7 |
| `streak` | ON | Milestones at 3 / 7 / 30; celebration-only |
| `pattern` | ON | Permutation test p<0.05, \|Δmood\|≥0.5, ≥10 tagged days |
| `change_point` | OFF (opt-in) | CUSUM, 5-day window, magnitude ≥ 0.8 mood / 1.5 energy |

### Algorithms
| Module | Technique | Lines (~) | Key constants |
|---|---|---|---|
| `von_mises_timing.py` | Circular KDE on hour-of-day | 50 | min_entries=7 |
| `skip_predictor.py` | sklearn `LogisticRegression` | 70 | features: `[hours_since_last, dow, entries_last_7d, nudge_was_shown]`; min_history=30 days; lazy import |
| `change_point.py` | CUSUM | 60 | window=5, magnitudes 0.8 / 1.5 |
| `bandit.py` | Thompson + Hawkes decay | 80 | `Beta(α,β)` informed priors per rule; τ_reminder=18h, τ_insight=72h |
| `pattern.py` (in rule) | Permutation test | 40 | shuffles=1000, p<0.05 |

### API surface (v1)
| Method | Path | Notes |
|---|---|---|
| GET | `/api/nudges` | Side-effecting: marks emissions as shown |
| POST | `/api/nudges/{id}/engaged` | Bandit update; id can be emission UUID or rule_id |
| POST | `/api/nudges/{id}/dismiss` | 24h decay |
| POST | `/api/nudges/{id}/snooze` | Snoozes rule until next 09:00 UTC |
| GET / PUT | `/api/preferences` | Replace-style PUT |
| GET | `/api/stats/retention` | `last_7d_active_days`, `last_30d_active_days`, `current_streak`, `best_streak`, `entries_per_active_week_median` |

### Defaults
- Quiet hours: **21:00 – 09:00** local (treated as UTC server-side; see Known Limitations).
- Engagement signal: **entry created within 30 minutes** of nudge marked `shown`. Frontend-attributed via `sessionStorage`.
- Onboarding shield: no nudges before entry #3.
- Hard cap: ≤ 1 nudge per response.

### Test coverage
- Backend: 18 vertical TDD slices, every rule + algorithm + route exercised. Banned-word copy assertions in CI.
- Frontend: 13 RTL slices covering NudgeStack/Card/Settings/Retention round-trips and tracker glue.
- Determinism: all algorithm tests use seeded RNGs.

### Performance characteristics
- `compute_nudges`: < 50 ms on 10k-entry JSON file.
- sklearn import is lazy (~300 ms) — paid once on first reminder evaluation.
- Permutation test: ~80 ms per tag at 1000 shuffles, n<1000 — cached when entry count grows by <5.

---

## Known Limitations (logged honestly)

1. **Timezone handling is naive.** Quiet hours and snooze targets use UTC. Will misbehave for non-UTC users until a TZ field is added to `Preferences`.
2. **Engagement signal conflates organic vs. nudge-driven logging.** A user who would log anyway gets credited to whichever nudge fired most recently. Mitigated (not solved) by `nudge_was_shown` feature in the skip-predictor.
3. **Skip-predictor is self-fulfilling.** Suppressing a reminder changes the label being learned.
4. **Single-process file writes.** No locking. Concurrent requests on a multi-process deployment would corrupt JSON state.
5. **No global error boundary on frontend.** A network failure in `/api/nudges` is swallowed silently — by design, but it does mean silent regressions are possible.
6. **Pattern nudges ON by default** despite cold-start risk; only the permutation gate stands between the user and a noisy first impression.
7. **Strict-mode double-render** is deduped via sessionStorage, but a clock skew between client and server could still register stale nudges.
8. **No telemetry.** We can verify *this* user's retention; we cannot measure feature adoption across the (nonexistent) user base.

---

## Future Scope

Ordered by leverage-to-effort ratio.

### Tier 1 — Earn before adding (post-30-days-of-data)
1. **Causal engagement attribution.** Replace the 30-min window heuristic with a holdout-based estimate: randomly suppress nudges 10% of the time, compare logging rates. Single-user, but week-over-week.
2. **Timezone-aware quiet hours and snooze.** Add `Preferences.timezone` (IANA), convert at the route layer. ~1 day.
3. **Atomic JSON writes.** Replace direct `write_text` with write-to-temp + `os.replace` if not already present. Defensive against future concurrency.
4. **Frontend error boundary** + dev-mode toast for nudge fetch failures.

### Tier 2 — Algorithmic depth, only if data justifies
5. **Contextual bandit** — replace per-rule Thompson sampling with LinUCB/Thompson over context features (`day_of_week`, `entries_last_7d`, `last_mood`). Useful only at >100 emissions.
6. **Bayesian online change-point** (BOCPD) replacing CUSUM. Better calibration of detection delay vs. false-alarm rate; ~150 lines.
7. **Tag-conditional uplift via permutation + multiple-testing correction** (Benjamini-Hochberg). Required as soon as users have >5 active tags, otherwise pattern nudges become a fishing expedition.
8. **Hierarchical priors** for the bandit using cross-rule data (still single-user). Faster cold start.

### Tier 3 — Product expansion
9. **Mood-aware planner integration** (brief #5) — surface change-point findings as planning prompts.
10. **Weekly digest view** (brief #2) — bundles insights and pattern findings on one screen, replaces ad-hoc nudge cards on the digest day.
11. **Voice / shortcut entry** to lower friction for the "logged within 30 min" attribution. iOS Shortcut + macOS quick-action.
12. **Export & import** of `.data/` for users who want to migrate or back up.

### Tier 4 — Only if the product becomes multi-user
13. Real auth + per-user state.
14. Push / email channels (FCM, SendGrid).
15. Cross-user A/B test framework with stratified randomization on activity tier.
16. Cohort-based informed priors (transfer learning across new users).
17. Privacy-preserving analytics (DP for aggregate retention reporting).

### Tier 5 — Speculative / research-grade
18. **Reinforcement learning over the full nudge timeline** (off-policy evaluation from logged data). Almost certainly overkill for a wellness app; documented for completeness.
19. **LLM-assisted copy generation** with strict template constraints + automated banned-word filter. Deferred until copy fatigue is a measured problem.
20. **Federated learning** of bandit priors across users without sending raw entries to a server.

---

## Decision log (one-liners)

| # | Decision | Rationale |
|---|---|---|
| D1 | All-on-demand, no scheduler | Matches single-user JSON architecture; zero ops cost |
| D2 | Engagement = entry within 30 min | Simplest defensible signal; documented tension |
| D3 | Pattern ON, change-point OFF by default | Pattern is gated by stats; change-point is sensitive |
| D4 | Two state files (`nudge_state`, `preferences`) | Mirrors existing `entries.json` convention |
| D5 | numpy + sklearn approved | von Mises + logistic regression need them; lazy-imported |
| D6 | Quiet hours 21:00–09:00 default | Conservative; user can override |
| D7 | ≤ 1 nudge per response, hard cap | Stacking is how products get uninstalled |
| D8 | Banned-word copy lists enforced in tests | The Duolingo guilt-trap is a *test* failure, not a vibe |

---

## Glossary

- **Onboarding shield** — engine returns `[]` while `len(entries) < 3`.
- **Engagement** — entry created within 30 min of a nudge being marked `shown`.
- **Cold start (bandit)** — first emission per rule, governed by informed `Beta(α,β)` priors.
- **Quiet hours** — wall-clock window during which the engine returns `[]` regardless of rule firings.
- **One-shot** — rule that fires at most once per user lifetime; tracked in `state.one_shot_fired`.
