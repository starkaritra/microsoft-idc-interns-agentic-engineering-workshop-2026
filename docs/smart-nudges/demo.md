# Smart Nudges — Demo Script

A step-by-step run-through that exercises every shipped feature. Total time: ~8 minutes. Reset between sections by deleting `backend/.data/`.

---

## 0. One-time setup (before the demo)

```powershell
# Backend
cd microsoft-idc-interns-agentic-engineering-workshop-2026\backend
.venv\Scripts\Activate.ps1     # or use the shared Skillup\.venv
pip install -r requirements.txt

# Frontend (separate terminal)
cd microsoft-idc-interns-agentic-engineering-workshop-2026\frontend
npm install
```

Open three terminals: **backend**, **frontend**, **scratch** (for `Invoke-RestMethod` calls).

---

## 1. Cold start — the onboarding shield (90 sec)

**What this proves:** new users get zero nudges. No spam on day one.

```powershell
# In backend terminal:
Remove-Item -Recurse -Force .data -ErrorAction SilentlyContinue
python -m uvicorn app.main:app --port 8000

# In frontend terminal:
npm run dev
```

1. Open http://localhost:5173 → Dashboard. No nudge card. No retention numbers worth showing. ✅
2. In scratch terminal:
   ```powershell
   Invoke-RestMethod http://localhost:8000/api/nudges | ConvertTo-Json -Depth 5
   ```
   → `{ "nudges": [] }` ✅
3. Log 2 entries via the **Log** page. Refresh dashboard. **Still no nudge** (onboarding gate is `< 3 entries`). ✅

> **Talking point:** "The first thing this system does is *nothing*. Onboarding is the product, not a nudge surface."

---

## 2. Seed data — the algorithms come alive (60 sec)

```powershell
# Backend terminal — stop uvicorn (Ctrl-C), then:
python seed.py
python -m uvicorn app.main:app --port 8000
```

Refresh dashboard.

1. **Retention panel** now shows real numbers — last-7d / last-30d active days, current streak, best streak, median entries-per-active-week. ✅
2. **Nudge card** appears (likely `first_insight` or `streak`, depending on seed).

> **Talking point:** "Every number on this panel is computed locally from your own entries. No analytics pipeline, no `users` table — just honest math."

---

## 3. The five rules in action (3 min)

Use scratch terminal to inspect state directly between actions:

```powershell
function Show-State { Get-Content .data\nudge_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 5 }
function Show-Prefs { Invoke-RestMethod http://localhost:8000/api/preferences | ConvertTo-Json -Depth 5 }
function Get-Nudges { Invoke-RestMethod http://localhost:8000/api/nudges | ConvertTo-Json -Depth 5 }
```

### 3a. Reminder (von Mises timing + skip-predictor)
- Show that all entries cluster around a specific hour (`Show-Prefs` if reminder override is null).
- Trigger `Get-Nudges` at that hour vs. far from it. Reminder appears only near typical logging time. ✅
- **If you just logged**, the skip-predictor suppresses the reminder. ✅

### 3b. Missing-entry
- With ≥ 3 entries and last entry > 24h ago → `missing_entry` nudge fires.
- Copy contains *no* loss-framing words ("missed", "broke", "lost"). Show by inspecting the response.

### 3c. First-insight (one-shot)
- After ~7 entries → fires once. State `one_shot_fired` array now contains `"first_insight"`. Subsequent calls never re-emit. ✅
  ```powershell
  Show-State
  ```

### 3d. Streak milestone (celebration-only)
- 3, 7, or 30 consecutive days → celebration nudge.
- Break a streak intentionally (skip a day in seed) → **no negative nudge fires**. The retention panel quietly shows `current_streak: 0`. ✅

### 3e. Pattern nudge (permutation-test gated)
- Pattern only fires when a tag has **n≥10 tagged days, p<0.05, |Δmood|≥0.5**. Most random data won't trigger it — that's the point.

### 3f. Change-point reflection (opt-in, OFF by default)
```powershell
$body = @{
  quiet_hours = @{ start = "21:00"; end = "09:00" }
  reminder_time_override = $null
  categories_enabled = @{ reminder=$true; missing_entry=$true; first_insight=$true; streak=$true; pattern=$true; change_point=$true }
} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri http://localhost:8000/api/preferences -Body $body -ContentType "application/json"
```
- After enabling, a planted mood dip in seed → reflection nudge with **curious** copy ("noticed a shift") not diagnostic ("you seem low"). ✅

---

## 4. The bandit learns from you (90 sec)

**What this proves:** the system self-tunes which nudge category *you* find useful.

1. Show current `rule_stats` in `Show-State` — `{ shown, engaged }` per rule.
2. Simulate engagement on one rule:
   ```powershell
   $rid = (Invoke-RestMethod http://localhost:8000/api/nudges).nudges[0].id
   Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/nudges/$rid/engaged"
   ```
3. Repeat a few times for one rule, dismiss for another. `Show-State` reveals the divergence.
4. Over subsequent calls, Thompson sampling shifts emissions toward the engaged rule. ✅

> **Talking point:** "No A/B infrastructure. No backend training job. The bandit converges on what works *for this user* in 20–30 emissions."

---

## 5. User control — the trust layer (60 sec)

Navigate to **/settings** in the browser.

1. Toggle off `pattern` → save → refresh dashboard → pattern nudge no longer surfaces. ✅
2. Set `reminder_time_override` to a specific time → that overrides the von Mises algorithm. ✅
3. Hit **"Disable all nudges"** (the trust escape hatch) → every category off in one click. ✅
4. Try invalid quiet hours (start == end) → client-side error, no PUT fires. Server would 422 anyway. ✅

In-card controls:
5. Click **Snooze** on a card → state writes `snoozed_until` to next 09:00 → that rule won't surface until then. ✅
6. Click **Dismiss** → 24h decay window starts for that rule. ✅

---

## 6. Honest retention dashboard (30 sec)

Scroll to the bottom of the dashboard:

| Stat | Meaning |
|---|---|
| Last 7d active days | Days with ≥1 entry in last week |
| Last 30d active days | Same, monthly |
| Current streak | Consecutive days ending today/yesterday |
| Best streak | All-time max consecutive run |
| Median entries / active week | Last 30d, ignoring inactive weeks |

> **Talking point:** "Priya asked for D1/D3/D7 retention numbers. In a single-user JSON-backed app, the *only* defensible answer is local. So we built the local answer. No fake dashboard."

---

## 7. Test suite (60 sec, optional)

```powershell
# Backend
cd backend
pytest -q

# Frontend
cd ..\frontend
npm test -- --run
```

Highlight in the output:
- Banned-word copy assertions (e.g. *"missed"*, *"broke"*, *"depressed"*, *"low mood"*).
- Seeded RNG tests for the bandit (deterministic convergence to higher-engagement arm).
- Permutation-test FPR check (planted-null gives ≤ 7% false positives across 100 seeds).

---

## Demo reset cheatsheet

```powershell
# Wipe state to demo "cold start" behavior again
cd backend
Remove-Item -Recurse -Force .data
python seed.py     # if you want seeded data back
```
