import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Dashboard from "../src/pages/Dashboard";

vi.mock("../src/lib/api", () => ({
  api: {
    stats: {
      daily: vi.fn().mockResolvedValue([]),
      heatmap: vi.fn().mockResolvedValue([]),
      retention: vi.fn().mockResolvedValue({
        last_7d_active_days: 0,
        last_30d_active_days: 0,
        current_streak: 0,
        best_streak: 0,
        entries_per_active_week_median: 0,
      }),
    },
    entries: {
      list: vi.fn().mockResolvedValue([]),
    },
    nudges: {
      list: vi.fn().mockResolvedValue({ nudges: [] }),
      engaged: vi.fn().mockResolvedValue(undefined),
      dismiss: vi.fn().mockResolvedValue(undefined),
      snooze: vi.fn().mockResolvedValue(undefined),
    },
  },
}));

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
}

describe("Dashboard", () => {
  it("shows loading state initially", () => {
    renderDashboard();
    expect(screen.getByText("Loading your pulse...")).toBeInTheDocument();
  });

  it("renders the dashboard heading after loading", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("shows 'No entries yet' message when no entries exist", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(
        screen.getByText("No entries yet. Start by logging your first mood!")
      ).toBeInTheDocument();
    });
  });

  it("shows summary cards after loading", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Today's Mood")).toBeInTheDocument();
      expect(screen.getByText("Today's Energy")).toBeInTheDocument();
      expect(screen.getByText("Entries Today")).toBeInTheDocument();
    });
  });
});
