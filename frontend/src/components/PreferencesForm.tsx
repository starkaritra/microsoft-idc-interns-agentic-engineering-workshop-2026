import { useState } from "react";
import {
  CATEGORY_LABELS,
  NUDGE_CATEGORIES,
  type CategoryToggles,
  type NudgeCategory,
  type Preferences,
} from "../lib/types";

interface Props {
  initial: Preferences;
  onSave: (prefs: Preferences) => Promise<void> | void;
}

function isValidQuietHours(start: string, end: string): boolean {
  return Boolean(start) && Boolean(end) && start !== end;
}

export default function PreferencesForm({ initial, onSave }: Props) {
  const [start, setStart] = useState(initial.quiet_hours.start);
  const [end, setEnd] = useState(initial.quiet_hours.end);
  const [override, setOverride] = useState<string>(
    initial.reminder_time_override ?? ""
  );
  const [categories, setCategories] = useState<CategoryToggles>(
    initial.categories_enabled
  );
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const quietValid = isValidQuietHours(start, end);
  const allDisabled = NUDGE_CATEGORIES.every((c) => !categories[c]);

  const toggleCategory = (cat: NudgeCategory) =>
    setCategories((c) => ({ ...c, [cat]: !c[cat] }));

  const disableAll = () => {
    const next: CategoryToggles = { ...categories };
    for (const c of NUDGE_CATEGORIES) next[c] = false;
    setCategories(next);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quietValid) return;
    setSaving(true);
    try {
      await onSave({
        quiet_hours: { start, end },
        reminder_time_override: override.trim() === "" ? null : override,
        categories_enabled: categories,
      });
      setSavedAt(Date.now());
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Trust escape hatch */}
      <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg p-3">
        <div>
          <p className="text-sm font-semibold text-gray-800">All nudges</p>
          <p className="text-xs text-gray-500">
            {allDisabled
              ? "All nudge categories are off."
              : "Turn off every category at once."}
          </p>
        </div>
        <button
          type="button"
          onClick={disableAll}
          disabled={allDisabled}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300
                     text-gray-700 hover:bg-white disabled:opacity-50
                     disabled:cursor-not-allowed cursor-pointer"
        >
          Disable all nudges
        </button>
      </div>

      {/* Quiet hours */}
      <fieldset>
        <legend className="text-sm font-semibold text-gray-800 mb-2">
          Quiet hours
        </legend>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs text-gray-600">
            Start
            <input
              type="time"
              aria-label="Quiet hours start"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-pulse-400"
            />
          </label>
          <label className="block text-xs text-gray-600">
            End
            <input
              type="time"
              aria-label="Quiet hours end"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-pulse-400"
            />
          </label>
        </div>
        {!quietValid ? (
          <p
            role="alert"
            className="text-xs text-amber-700 mt-2"
          >
            Quiet hours start and end must be different.
          </p>
        ) : null}
      </fieldset>

      {/* Reminder override */}
      <label className="block">
        <span className="text-sm font-semibold text-gray-800">
          Reminder time override
        </span>
        <span className="block text-xs text-gray-500 mb-1">
          Leave blank to use the personalized time.
        </span>
        <input
          type="time"
          aria-label="Reminder time override"
          value={override}
          onChange={(e) => setOverride(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                     focus:outline-none focus:ring-2 focus:ring-pulse-400"
        />
      </label>

      {/* Categories */}
      <fieldset>
        <legend className="text-sm font-semibold text-gray-800 mb-2">
          Categories
        </legend>
        <div className="space-y-2">
          {NUDGE_CATEGORIES.map((cat) => (
            <label
              key={cat}
              className="flex items-center justify-between p-2 rounded-lg
                         hover:bg-gray-50 cursor-pointer"
            >
              <span className="text-sm text-gray-800">
                {CATEGORY_LABELS[cat]}
              </span>
              <input
                type="checkbox"
                aria-label={CATEGORY_LABELS[cat]}
                checked={categories[cat]}
                onChange={() => toggleCategory(cat)}
                className="h-4 w-4 accent-pulse-600 cursor-pointer"
              />
            </label>
          ))}
        </div>
      </fieldset>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={!quietValid || saving}
          className="px-4 py-2 rounded-lg bg-pulse-600 text-white text-sm
                     font-semibold hover:bg-pulse-700 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {saving ? "Saving..." : "Save preferences"}
        </button>
        {savedAt ? (
          <span
            role="status"
            className="text-sm text-emerald-700"
          >
            Saved
          </span>
        ) : null}
      </div>
    </form>
  );
}
