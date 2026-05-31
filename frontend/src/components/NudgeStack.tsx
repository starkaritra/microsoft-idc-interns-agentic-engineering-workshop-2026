import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { pruneStale, recordNudgeShown } from "../lib/nudgeTracking";
import type { Nudge } from "../lib/types";
import NudgeCard from "./NudgeCard";

/**
 * Fetches nudges from the API and renders at most one. A broken nudge feature
 * must never break the dashboard — all errors are swallowed.
 */
export default function NudgeStack() {
  const [nudge, setNudge] = useState<Nudge | null>(null);

  useEffect(() => {
    let cancelled = false;
    pruneStale();
    try {
      api.nudges
        .list()
        .then((res) => {
          if (cancelled) return;
          const first = res.nudges?.[0] ?? null;
          setNudge(first);
          if (first) recordNudgeShown(first.id);
        })
        .catch(() => {
          // Silent failure — nudges are non-critical.
        });
    } catch {
      // api.nudges may be missing in some test mocks; fail silent.
    }
    return () => {
      cancelled = true;
    };
  }, []);

  if (!nudge) return null;

  const handleDismiss = () => {
    setNudge(null);
    api.nudges.dismiss(nudge.rule_id).catch(() => {});
  };

  const handleSnooze = () => {
    setNudge(null);
    api.nudges.snooze(nudge.rule_id).catch(() => {});
  };

  return (
    <div data-testid="nudge-stack">
      <NudgeCard
        nudge={nudge}
        onDismiss={handleDismiss}
        onSnooze={handleSnooze}
      />
    </div>
  );
}
