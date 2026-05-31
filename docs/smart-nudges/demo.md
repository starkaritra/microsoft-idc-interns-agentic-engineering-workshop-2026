# Smart Nudges — Demo Script

Browser-only walkthrough. No terminal juggling during the demo. Practice once end-to-end before going live.

---

## Pre-demo checklist

- [ ] Backend running: `python seed.py` then `python -m uvicorn app.main:app --port 8000`
- [ ] Frontend running: `npm run dev`
- [ ] Three browser tabs open:
  - **Tab 1:** http://localhost:5173 (the app — Dashboard)
  - **Tab 2:** http://localhost:5173/settings (Settings page)
  - **Tab 3:** http://localhost:8000/docs (FastAPI explorer)
- [ ] Browser zoom 110–125% so the audience can read.
- [ ] Speaker notes (`pitch.md`) open in another window.

---

## Act 1 — The Problem

**Tab 1: Dashboard.** Don't touch anything yet.

Say:
> "Pulse loses 7 of 10 users between Day 3 and Day 7. The obvious fix — 'send more reminders' — is also the fastest way to get uninstalled. I built a nudge system that earns attention instead of demanding it."

Point at:
- The nudge card at the top — ≤ 1 visible by design.
- The Retention panel further down — the *honest* numbers we can defend in a single-user app.

> "Five behavioral rules, four lightweight algorithms, and one hard cap: never more than one nudge at a time."

---

## Act 2 — The Trust Layer

**Switch to Tab 2 (Settings).**

> "Before I show what the system does, let me show what the *user* can do."

1. Point at the **category toggles** — six independent on/off switches.
2. Point at **quiet hours** and **reminder time override**.
3. Hit **"Disable all nudges"** → switch to Tab 1, refresh → card gone.
4. Switch back to Tab 2 → re-enable → Tab 1 refresh → card returns.

Say:
> "One tap silences the entire system. Every default in this build optimizes for *not getting turned off* — because a nudge engine the user disabled is worth zero."

---

## Act 3 — The Five Rules and the Math Behind Them

Pull up `pitch.md` Slide 3 (the algorithm table) on screen as a visual aid if you can.

**Stay on Tab 1.** Walk through what's visible right now:

1. Read the current nudge card's title and body out loud. Identify its rule.
2. For each of the five rules, give a one-sentence pitch — even if it's not currently visible:

| Rule | What it does | The algorithm |
|---|---|---|
| `reminder` | Daily check-in | **von Mises KDE** learns your circadian logging mode (handles 23→0 wrap-around) |
| `missing_entry` | Gentle prompt after 24h silence | Only after entry #3 (onboarding shield) |
| `first_insight` | One-shot celebration at entry #7 | The "give back" moment |
| `streak` | 3 / 7 / 30-day celebrations | **Never** loss-framed — enforced by tests, not vibes |
| `pattern` | "You score +0.8 mood on `exercise` days, p<0.05" | **Permutation test**, 1000 shuffles |

3. **The skip-predictor:**
> "There's a fifth algorithm that decides whether to fire at all. A logistic regression predicts P(you'll log anyway today). If it's high, the reminder stays silent. That kills the #1 spam vector."

4. **The bandit:**
> "When multiple rules compete, a Thompson-sampled bandit picks based on *your* engagement history. It self-tunes in 20–30 emissions. No A/B framework needed."

---

## Act 4 — Show, Don't Tell

Live interaction.

1. **Tab 1:** click **Snooze** on the visible nudge → card disappears.
2. Refresh → still gone. Say: "Snoozed until 9am tomorrow."
3. **Tab 2 (Settings):** toggle off the snoozed rule's category, save → switch to Tab 1, refresh.
   - Either a *different* rule's nudge appears (great — proves rotation) or none (also fine — "the system would rather show nothing than show noise").
4. Re-enable in Tab 2.

5. **Scroll down on Tab 1 to the Retention panel.** Walk through:
   - Last 7d active days
   - Last 30d active days
   - Current streak
   - Best streak
   - Median entries per active week

Say:
> "Priya asked for D1/D3/D7 retention. In a single-user JSON-backed app, the only defensible answer is local. So we built it. No fake dashboard, no analytics theater."

---

## Act 5 — Under the Hood *(technical audiences only)*

**Switch to Tab 3 (FastAPI /docs).**

> "Every panel you saw is a thin view over these endpoints. No hidden state."

Live-call two endpoints — pick the highest-impact two, don't run all of them:

1. **`GET /api/nudges`** → *Try it out* → *Execute*. Show the JSON: `id`, `rule_id`, `priority`, `emitted_at`.
2. **`GET /api/stats/retention`** → *Try it out* → *Execute*. Same numbers as the Retention panel — proves the UI isn't lying.

---

## Act 6 — Honest Trade-offs

Back to your speaker notes (`pitch.md` Slide 5).

Say:
> "Three decisions I want to flag honestly:
> 1. The engagement signal — 'entry within 30 min of nudge' — conflates organic logging with nudge-driven logging.
> 2. Pattern nudges are on by default, gated only by a permutation test. Cold-start risk is real.
> 3. The skip-predictor is self-fulfilling — suppressing a reminder changes the label being learned.
>
> All of these are in `spec_and_future_scope.md`. The principle: a nudge engine the user disabled is worth zero — regardless of how clever its math is."

---

## The two rules that save you live

1. **"If nothing fires, that's also the demo — the system would rather show nothing than show noise."** Memorize this. Skip and move on.
2. **Never open a terminal during the demo.** If state is wrong, reset it *before* you go live:
   ```powershell
   cd backend
   Remove-Item -Recurse -Force .data
   python seed.py
   python -m uvicorn app.main:app --port 8000
   ```
