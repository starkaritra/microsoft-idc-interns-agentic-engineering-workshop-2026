# Frontend Handoff — Smart Nudges

**Reads from:** `integration.md` (contract). **Owner:** frontend.
**Stack:** React 18 · Vite · TypeScript · Tailwind · React Router · Vitest + React Testing Library.

This doc describes *what* to build and *in what order*, using TDD tracer-bullet slices. The UI is intentionally minimal — one card at a time, dismissible, with a settings page. No animations beyond Tailwind transitions.

---

## Module map

```
frontend/src/
  components/
    NudgeStack.tsx        # max 1 visible; renders nothing if list empty
    NudgeCard.tsx         # title, body, CTA, dismiss, snooze
    PreferencesForm.tsx   # quiet hours, reminder override, category toggles
    RetentionPanel.tsx    # last 7/30d active days, current streak
  pages/
    Settings.tsx          # uses PreferencesForm
    Dashboard.tsx         # MODIFY: mount <NudgeStack /> above existing content;
                          #         mount <RetentionPanel /> below charts
  lib/
    api.ts                # MODIFY: add nudges + preferences + retention clients
    types.ts              # MODIFY: add Nudge, Preferences, RetentionStats
    nudgeTracking.ts      # records "entry created within 30 min of nudge shown"
```

**Public interfaces (the only things component tests touch):**
- `<NudgeStack />` — fetches from `/api/nudges` on mount; renders 0 or 1 `<NudgeCard />`.
- `<NudgeCard nudge onDismiss onSnooze onCtaClick />` — pure presentational.
- `<PreferencesForm initial onSave />` — controlled form.
- `<RetentionPanel />` — fetches `/api/stats/retention` on mount.

---

## Files to add / modify

**Add:** all components above, `pages/Settings.tsx`, `lib/nudgeTracking.ts`, plus tests under `frontend/tests/`.

**Modify:**
- `App.tsx` — add `/settings` route.
- `components/Layout.tsx` — add `Settings` link to nav.
- `pages/Dashboard.tsx` — mount `<NudgeStack />` and `<RetentionPanel />`.
- `pages/LogEntry.tsx` — on successful entry create, call `nudgeTracking.recordEntryCreated()`.
- `lib/api.ts`, `lib/types.ts` — extend with new endpoints/types.

**Do not modify:** existing chart/components, existing entry models on the wire (the contract is additive).

---

## Engagement tracking (client-side glue for the engagement signal)

The engagement signal is **"entry created within 30 minutes of nudge shown"**. The frontend owns this correlation:

1. `<NudgeStack />` stores `{nudge_id, shown_at}` in `sessionStorage` for every nudge it renders.
2. `nudgeTracking.recordEntryCreated()` (called from `LogEntry` after a successful `POST /api/entries`) scans sessionStorage for nudges shown in the last 30 min and POSTs `/api/nudges/{id}/engaged` for each, then clears them.
3. Stale nudges (> 30 min) are pruned on every `<NudgeStack />` mount.

This keeps the backend dumb — the server records what the client tells it.

> **Trust note (documented in `integration.md`):** this signal conflates organic logging with nudge-driven logging. It is the chosen design. Do not "improve" by waiting for an explicit CTA tap — that contradicts the locked decision.

---

## TDD tracer-bullet plan (ordered)

Use Vitest + RTL. Mock the network with `vi.fn()` on `fetch` or via the existing `api.ts` shape. Each slice = one test → minimal component code.

### Slice 1 — NudgeStack renders nothing when API returns `[]`
- **Test:** mock `/api/nudges` → `{nudges: []}`; expect `screen.queryByTestId("nudge-card")` to be `null`.
- **Code:** `<NudgeStack />` skeleton + fetch on mount.

### Slice 2 — NudgeStack renders exactly one card when API returns one
- **Test:** mock returns one nudge with title "Morning check-in"; expect title visible; expect only one `nudge-card` testid.
- **Code:** Render first item only. (Backend already caps at 1, but we cap defensively.)

### Slice 3 — Card shows title, body, CTA label
- **Test:** assert all three are in DOM; CTA renders as a link to `nudge.cta.route`.
- **Code:** `<NudgeCard />`.

### Slice 4 — Dismiss button POSTs to `/dismiss` and removes card
- **Test:** click Dismiss → POST called with rule_id → card no longer in DOM.
- **Code:** dismiss handler + optimistic removal.

### Slice 5 — Snooze button POSTs to `/snooze` and removes card
- **Test:** symmetrical to Slice 4.

### Slice 6 — `nudgeTracking.recordEntryCreated` fires `/engaged` for recent nudges
- **Test:** seed sessionStorage with two nudges (one 10 min ago, one 40 min ago); call `recordEntryCreated()`; expect POST to `/engaged` only for the recent one; expect sessionStorage cleared of the recent one (stale entries also pruned).
- **Code:** `lib/nudgeTracking.ts`.

### Slice 7 — LogEntry calls tracker on success
- **Test:** mount `LogEntry`, submit a valid entry, mock POST `/api/entries` to resolve; assert `recordEntryCreated` was called.
- **Code:** wire the call in `LogEntry.tsx` after successful submit.

### Slice 8 — Settings page renders preferences from API
- **Test:** mock `GET /api/preferences` → fixture; assert quiet-hours inputs prefilled, all category toggles reflect state.
- **Code:** `pages/Settings.tsx` + `<PreferencesForm />`.

### Slice 9 — Saving preferences PUTs and shows confirmation
- **Test:** toggle a category, change quiet hours start, click Save → assert PUT called with merged payload, success message appears.
- **Code:** form submit + toast.

### Slice 10 — Preferences form rejects invalid quiet hours
- **Test:** set start == end → Save button disabled or shows inline error; no PUT fires.
- **Code:** client-side validation matching backend's 422.

### Slice 11 — RetentionPanel renders stats from API
- **Test:** mock `GET /api/stats/retention` with sample payload; assert each stat is visible with the right label.
- **Code:** `<RetentionPanel />`.

### Slice 12 — Layout exposes Settings nav link
- **Test:** render `<Layout>`, assert link with text "Settings" exists with `href="/settings"`.
- **Code:** modify `Layout.tsx`.

### Slice 13 — Dashboard mounts NudgeStack above content
- **Test:** mount `<Dashboard />` with mocked API responses; assert NudgeStack region appears before chart region in DOM order.
- **Code:** modify `Dashboard.tsx`.

---

## UX rules (binding — derived from `integration.md` copy rules)

- One nudge visible at a time. Never stack.
- Dismiss is a single tap; no confirmation dialog.
- The card is never modal; it sits inline above the dashboard.
- Banned UI patterns: countdown timers, red urgency colors, "don't lose your streak"-style copy. Tailwind: use neutral/green palette, never red for nudges.
- Settings has a single "Disable all nudges" button at the top that toggles every category at once — the trust escape hatch.

---

## Test conventions

- Tests live in `frontend/tests/`, mirroring component names.
- Use the existing `setup.ts` and `vi.mock` patterns from `Dashboard.test.tsx`.
- Do not mock `<NudgeCard />` inside `<NudgeStack />` tests — render the real subtree (per `tdd/mocking.md` guidance: integration-style tests).
- For sessionStorage, use the real one in jsdom (don't mock it).
- All async assertions go through `findBy*` / `waitFor`.

## Non-goals for this handoff

- No animations, no toast library, no design-system extraction. Tailwind utility classes only.
- No client-side state library (no Redux/Zustand). `useState` + `useEffect` are sufficient.
- No service worker / push registration.
- No telemetry beyond the engagement POST.

## Risks for frontend specifically

- **Strict-mode double-render of `<NudgeStack />`** could double-mark nudges as shown. Mitigate: dedupe by `nudge.id` in sessionStorage before POSTing.
- **Tab open across midnight** during local quiet hours change — Settings form should re-fetch on focus to avoid stale prefs.
- **No global error boundary** — wrap network calls and fail silently for nudges (a broken nudge feature must not break the dashboard).
