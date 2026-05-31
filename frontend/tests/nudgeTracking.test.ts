import { beforeEach, describe, expect, it, vi } from "vitest";

const mockEngaged = vi.fn();
vi.mock("../src/lib/api", () => ({
  api: {
    nudges: {
      engaged: (...a: unknown[]) => mockEngaged(...a),
    },
  },
}));

import {
  ENGAGEMENT_WINDOW_MS,
  pruneStale,
  recordEntryCreated,
  recordNudgeShown,
} from "../src/lib/nudgeTracking";

const KEY = "pulse.nudges.shown";

describe("nudgeTracking", () => {
  beforeEach(() => {
    sessionStorage.clear();
    mockEngaged.mockReset().mockResolvedValue(undefined);
  });

  it("recordNudgeShown adds an entry", () => {
    recordNudgeShown("n-1", 1000);
    const stored = JSON.parse(sessionStorage.getItem(KEY)!);
    expect(stored).toEqual([{ nudge_id: "n-1", shown_at: 1000 }]);
  });

  it("recordNudgeShown dedupes by nudge_id (StrictMode safe)", () => {
    recordNudgeShown("n-1", 1000);
    recordNudgeShown("n-1", 2000);
    const stored = JSON.parse(sessionStorage.getItem(KEY)!);
    expect(stored).toHaveLength(1);
    expect(stored[0].shown_at).toBe(2000);
  });

  it("pruneStale removes records older than 30 min", () => {
    const now = 1_000_000_000;
    sessionStorage.setItem(
      KEY,
      JSON.stringify([
        { nudge_id: "fresh", shown_at: now - 10 * 60 * 1000 },
        { nudge_id: "stale", shown_at: now - 40 * 60 * 1000 },
      ])
    );
    pruneStale(now);
    const stored = JSON.parse(sessionStorage.getItem(KEY)!);
    expect(stored.map((r: { nudge_id: string }) => r.nudge_id)).toEqual([
      "fresh",
    ]);
  });

  it("recordEntryCreated POSTs /engaged only for recent nudges and clears them", async () => {
    const now = 1_000_000_000;
    sessionStorage.setItem(
      KEY,
      JSON.stringify([
        { nudge_id: "recent", shown_at: now - 10 * 60 * 1000 },
        { nudge_id: "stale", shown_at: now - 40 * 60 * 1000 },
      ])
    );
    await recordEntryCreated(now);
    expect(mockEngaged).toHaveBeenCalledTimes(1);
    expect(mockEngaged).toHaveBeenCalledWith("recent");
    expect(JSON.parse(sessionStorage.getItem(KEY)!)).toEqual([]);
  });

  it("recordEntryCreated swallows API errors", async () => {
    mockEngaged.mockRejectedValue(new Error("nope"));
    sessionStorage.setItem(
      KEY,
      JSON.stringify([{ nudge_id: "n", shown_at: Date.now() }])
    );
    await expect(recordEntryCreated()).resolves.toBeUndefined();
  });

  it("ENGAGEMENT_WINDOW_MS is 30 minutes", () => {
    expect(ENGAGEMENT_WINDOW_MS).toBe(30 * 60 * 1000);
  });
});
