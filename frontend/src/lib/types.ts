export interface Entry {
  id: string;
  mood: number;
  energy: number;
  note: string | null;
  tags: string[];
  timestamp: string;
}

export interface EntryCreate {
  mood: number;
  energy: number;
  note?: string;
  tags: string[];
}

export interface DailyStat {
  date: string;
  avg_mood: number | null;
  avg_energy: number | null;
  count: number;
}

export interface WeeklyStat {
  week_start: string;
  avg_mood: number | null;
  avg_energy: number | null;
  count: number;
}

export interface HeatmapDay {
  date: string;
  avg_mood: number | null;
  count: number;
}

export interface TagsResponse {
  predefined: string[];
  custom: string[];
}

export const MOOD_EMOJIS: Record<number, string> = {
  1: "😢",
  2: "😕",
  3: "😐",
  4: "🙂",
  5: "😄",
};

export const MOOD_LABELS: Record<number, string> = {
  1: "Awful",
  2: "Bad",
  3: "Okay",
  4: "Good",
  5: "Great",
};

// ---- Smart Nudges ----

export type NudgeCategory =
  | "reminder"
  | "missing_entry"
  | "first_insight"
  | "streak"
  | "pattern"
  | "change_point";

export interface NudgeCta {
  label: string;
  route: string;
}

export interface Nudge {
  id: string;
  rule_id: string;
  category: NudgeCategory | string;
  title: string;
  body: string;
  cta?: NudgeCta | null;
  priority: number;
  emitted_at: string;
}

export interface NudgesResponse {
  nudges: Nudge[];
}

export interface QuietHours {
  start: string; // "HH:MM"
  end: string;
}

export type CategoryToggles = Record<NudgeCategory, boolean>;

export interface Preferences {
  quiet_hours: QuietHours;
  reminder_time_override: string | null; // "HH:MM" or null
  categories_enabled: CategoryToggles;
}

export interface RetentionStats {
  last_7d_active_days: number;
  last_30d_active_days: number;
  current_streak: number;
  best_streak: number;
  entries_per_active_week_median: number;
}

export const NUDGE_CATEGORIES: NudgeCategory[] = [
  "reminder",
  "missing_entry",
  "first_insight",
  "streak",
  "pattern",
  "change_point",
];

export const CATEGORY_LABELS: Record<NudgeCategory, string> = {
  reminder: "Daily reminder",
  missing_entry: "Missing entry",
  first_insight: "First insight",
  streak: "Streak celebration",
  pattern: "Pattern discovery",
  change_point: "Reflection prompt",
};
