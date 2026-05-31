import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NudgeStack from "../src/components/NudgeStack";
import type { Nudge } from "../src/lib/types";

const mockList = vi.fn();
const mockDismiss = vi.fn();
const mockSnooze = vi.fn();
const mockEngaged = vi.fn();

vi.mock("../src/lib/api", () => ({
  api: {
    nudges: {
      list: (...a: unknown[]) => mockList(...a),
      dismiss: (...a: unknown[]) => mockDismiss(...a),
      snooze: (...a: unknown[]) => mockSnooze(...a),
      engaged: (...a: unknown[]) => mockEngaged(...a),
    },
  },
}));

const nudge: Nudge = {
  id: "n-1",
  rule_id: "reminder",
  category: "reminder",
  title: "Morning check-in",
  body: "How are you starting the day?",
  cta: { label: "Log now", route: "/log" },
  priority: 0.8,
  emitted_at: "2026-05-31T09:00:00Z",
};

function renderStack() {
  return render(
    <MemoryRouter>
      <NudgeStack />
    </MemoryRouter>
  );
}

describe("NudgeStack", () => {
  beforeEach(() => {
    mockList.mockReset();
    mockDismiss.mockReset().mockResolvedValue(undefined);
    mockSnooze.mockReset().mockResolvedValue(undefined);
    mockEngaged.mockReset().mockResolvedValue(undefined);
    sessionStorage.clear();
  });

  it("renders nothing when API returns []", async () => {
    mockList.mockResolvedValue({ nudges: [] });
    renderStack();
    await waitFor(() => expect(mockList).toHaveBeenCalled());
    expect(screen.queryByTestId("nudge-card")).toBeNull();
  });

  it("renders exactly one card when API returns one nudge", async () => {
    mockList.mockResolvedValue({ nudges: [nudge] });
    renderStack();
    await screen.findByTestId("nudge-card");
    expect(screen.getAllByTestId("nudge-card")).toHaveLength(1);
    expect(screen.getByText("Morning check-in")).toBeInTheDocument();
  });

  it("renders only the first when API returns multiple (defensive cap)", async () => {
    mockList.mockResolvedValue({
      nudges: [nudge, { ...nudge, id: "n-2", title: "Second" }],
    });
    renderStack();
    await screen.findByTestId("nudge-card");
    expect(screen.getAllByTestId("nudge-card")).toHaveLength(1);
    expect(screen.queryByText("Second")).toBeNull();
  });

  it("dismiss removes the card and POSTs with rule_id", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue({ nudges: [nudge] });
    renderStack();
    await screen.findByTestId("nudge-card");
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => {
      expect(mockDismiss).toHaveBeenCalledWith("reminder");
    });
    expect(screen.queryByTestId("nudge-card")).toBeNull();
  });

  it("snooze removes the card and POSTs with rule_id", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue({ nudges: [nudge] });
    renderStack();
    await screen.findByTestId("nudge-card");
    await user.click(screen.getByRole("button", { name: "Snooze" }));
    await waitFor(() => {
      expect(mockSnooze).toHaveBeenCalledWith("reminder");
    });
    expect(screen.queryByTestId("nudge-card")).toBeNull();
  });

  it("records the shown nudge in sessionStorage", async () => {
    mockList.mockResolvedValue({ nudges: [nudge] });
    renderStack();
    await screen.findByTestId("nudge-card");
    const raw = sessionStorage.getItem("pulse.nudges.shown");
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed).toHaveLength(1);
    expect(parsed[0].nudge_id).toBe("n-1");
  });

  it("does not break the dashboard if API throws", async () => {
    mockList.mockRejectedValue(new Error("boom"));
    renderStack();
    await waitFor(() => expect(mockList).toHaveBeenCalled());
    expect(screen.queryByTestId("nudge-card")).toBeNull();
  });
});
