import { api } from "./api";

/**
 * Client-side correlation of "entry created within 30 minutes of nudge shown".
 * The backend is dumb: it records what we tell it.
 *
 * Stored shape in sessionStorage under SHOWN_KEY:
 *   Array<{ nudge_id: string; shown_at: number }>
 *
 * `shown_at` is `Date.now()` (epoch ms) for simple math.
 */

const SHOWN_KEY = "pulse.nudges.shown";
export const ENGAGEMENT_WINDOW_MS = 30 * 60 * 1000;

interface ShownRecord {
  nudge_id: string;
  shown_at: number;
}

function read(): ShownRecord[] {
  try {
    const raw = sessionStorage.getItem(SHOWN_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (r): r is ShownRecord =>
        r &&
        typeof r.nudge_id === "string" &&
        typeof r.shown_at === "number"
    );
  } catch {
    return [];
  }
}

function write(records: ShownRecord[]): void {
  try {
    sessionStorage.setItem(SHOWN_KEY, JSON.stringify(records));
  } catch {
    // sessionStorage may be unavailable (private mode, quota); fail silent.
  }
}

/** Remove records older than the engagement window. */
export function pruneStale(now: number = Date.now()): void {
  const fresh = read().filter((r) => now - r.shown_at <= ENGAGEMENT_WINDOW_MS);
  write(fresh);
}

/** Record a nudge as shown. Deduped by nudge_id (StrictMode-safe). */
export function recordNudgeShown(
  nudgeId: string,
  now: number = Date.now()
): void {
  const records = read().filter(
    (r) => r.nudge_id !== nudgeId && now - r.shown_at <= ENGAGEMENT_WINDOW_MS
  );
  records.push({ nudge_id: nudgeId, shown_at: now });
  write(records);
}

/**
 * Called after a successful entry create. For every nudge shown within the
 * engagement window, POST /engaged and remove the record. Stale records are
 * pruned too.
 */
export async function recordEntryCreated(
  now: number = Date.now()
): Promise<void> {
  const records = read();
  const recent = records.filter((r) => now - r.shown_at <= ENGAGEMENT_WINDOW_MS);
  // Clear storage immediately so retries/concurrent calls don't double-fire.
  write([]);
  await Promise.all(
    recent.map((r) =>
      api.nudges.engaged(r.nudge_id).catch(() => {
        // Failing to record engagement must not break the entry flow.
      })
    )
  );
}

/** Test helper. */
export function _clearAllShown(): void {
  write([]);
}
