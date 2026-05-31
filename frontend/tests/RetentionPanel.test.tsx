import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RetentionPanel from "../src/components/RetentionPanel";

const mockRetention = vi.fn();
vi.mock("../src/lib/api", () => ({
  api: {
    stats: {
      retention: (...a: unknown[]) => mockRetention(...a),
    },
  },
}));

describe("RetentionPanel", () => {
  beforeEach(() => {
    mockRetention.mockReset();
  });

  it("renders stats from API", async () => {
    mockRetention.mockResolvedValue({
      last_7d_active_days: 5,
      last_30d_active_days: 18,
      current_streak: 3,
      best_streak: 12,
      entries_per_active_week_median: 4,
    });
    render(<RetentionPanel />);
    expect(await screen.findByText("5")).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("3d")).toBeInTheDocument();
    expect(screen.getByText("12d")).toBeInTheDocument();
    expect(screen.getByText("Active days (7d)")).toBeInTheDocument();
    expect(
      screen.getByText("Median entries / active week")
    ).toBeInTheDocument();
  });

  it("renders nothing when API fails", async () => {
    mockRetention.mockRejectedValue(new Error("nope"));
    const { container } = render(<RetentionPanel />);
    // Wait a tick for the rejected promise.
    await new Promise((r) => setTimeout(r, 0));
    expect(container.firstChild).toBeNull();
  });
});
