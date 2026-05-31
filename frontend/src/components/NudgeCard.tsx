import { Link } from "react-router-dom";
import type { Nudge } from "../lib/types";

interface Props {
  nudge: Nudge;
  onDismiss: () => void;
  onSnooze: () => void;
  onCtaClick?: () => void;
}

/**
 * Pure presentational nudge card. Neutral / green palette only — never red.
 * No countdown timers, no loss framing.
 */
export default function NudgeCard({
  nudge,
  onDismiss,
  onSnooze,
  onCtaClick,
}: Props) {
  return (
    <div
      data-testid="nudge-card"
      data-rule-id={nudge.rule_id}
      className="bg-emerald-50 border border-emerald-200 rounded-xl p-4
                 flex flex-col sm:flex-row sm:items-center gap-3"
    >
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-semibold text-emerald-900">
          {nudge.title}
        </h3>
        <p className="text-sm text-gray-700 mt-0.5">{nudge.body}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {nudge.cta ? (
          <Link
            to={nudge.cta.route}
            onClick={onCtaClick}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm
                       font-medium hover:bg-emerald-700 transition-colors"
          >
            {nudge.cta.label}
          </Link>
        ) : null}
        <button
          type="button"
          onClick={onSnooze}
          className="px-2.5 py-1.5 rounded-lg text-sm text-gray-600
                     hover:bg-gray-100 transition-colors cursor-pointer"
        >
          Snooze
        </button>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          className="px-2.5 py-1.5 rounded-lg text-sm text-gray-600
                     hover:bg-gray-100 transition-colors cursor-pointer"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
