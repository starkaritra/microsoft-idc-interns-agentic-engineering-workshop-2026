import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { RetentionStats } from "../lib/types";

interface Stat {
  label: string;
  value: string | number;
}

export default function RetentionPanel() {
  const [stats, setStats] = useState<RetentionStats | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    try {
      api.stats
        .retention()
        .then((s) => {
          if (!cancelled) setStats(s);
        })
        .catch(() => {
          if (!cancelled) setError(true);
        });
    } catch {
      if (!cancelled) setError(true);
    }
    return () => {
      cancelled = true;
    };
  }, []);

  if (error || !stats) return null;

  const items: Stat[] = [
    { label: "Active days (7d)", value: stats.last_7d_active_days },
    { label: "Active days (30d)", value: stats.last_30d_active_days },
    { label: "Current streak", value: `${stats.current_streak}d` },
    { label: "Best streak", value: `${stats.best_streak}d` },
    {
      label: "Median entries / active week",
      value: stats.entries_per_active_week_median,
    },
  ];

  return (
    <section
      data-testid="retention-panel"
      className="bg-white rounded-xl border border-gray-200 p-4"
    >
      <h2 className="text-lg font-semibold text-gray-800 mb-3">
        Your consistency
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {items.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-2xl font-bold text-pulse-600">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
