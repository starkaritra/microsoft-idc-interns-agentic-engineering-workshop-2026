import { useEffect, useState } from "react";
import PreferencesForm from "../components/PreferencesForm";
import { api } from "../lib/api";
import type { Preferences } from "../lib/types";

export default function Settings() {
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    api.preferences
      .get()
      .then((p) => {
        setPrefs(p);
        setError(null);
      })
      .catch(() => setError("Could not load preferences."));
  };

  useEffect(() => {
    load();
    // Re-fetch on focus (e.g. tab open across midnight / quiet-hours change).
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  const handleSave = async (next: Preferences) => {
    const updated = await api.preferences.update(next);
    setPrefs(updated);
  };

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
      <p className="text-sm text-gray-500 mb-6">
        Control how and when Pulse nudges you.
      </p>
      {error ? (
        <p role="alert" className="text-sm text-amber-700 mb-4">
          {error}
        </p>
      ) : null}
      {prefs ? (
        <PreferencesForm initial={prefs} onSave={handleSave} />
      ) : !error ? (
        <p className="text-gray-400 text-sm">Loading preferences...</p>
      ) : null}
    </div>
  );
}
