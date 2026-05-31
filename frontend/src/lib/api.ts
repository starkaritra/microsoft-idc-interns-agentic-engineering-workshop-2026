import type {
  DailyStat,
  Entry,
  EntryCreate,
  HeatmapDay,
  NudgesResponse,
  Preferences,
  RetentionStats,
  TagsResponse,
  WeeklyStat,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  entries: {
    list: (startDate?: string, endDate?: string) => {
      const params = new URLSearchParams();
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      const qs = params.toString();
      return request<Entry[]>(`/entries${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => request<Entry>(`/entries/${id}`),
    create: (data: EntryCreate) =>
      request<Entry>("/entries", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/entries/${id}`, { method: "DELETE" }),
  },
  stats: {
    daily: () => request<DailyStat[]>("/stats/daily"),
    weekly: () => request<WeeklyStat[]>("/stats/weekly"),
    heatmap: () => request<HeatmapDay[]>("/stats/heatmap"),
    retention: () => request<RetentionStats>("/stats/retention"),
  },
  tags: () => request<TagsResponse>("/tags"),
  nudges: {
    list: () => request<NudgesResponse>("/nudges"),
    engaged: (nudgeId: string) =>
      request<void>(`/nudges/${nudgeId}/engaged`, { method: "POST" }),
    dismiss: (ruleId: string) =>
      request<void>(`/nudges/${ruleId}/dismiss`, { method: "POST" }),
    snooze: (ruleId: string) =>
      request<void>(`/nudges/${ruleId}/snooze`, { method: "POST" }),
  },
  preferences: {
    get: () => request<Preferences>("/preferences"),
    update: (prefs: Preferences) =>
      request<Preferences>("/preferences", {
        method: "PUT",
        body: JSON.stringify(prefs),
      }),
  },
};
