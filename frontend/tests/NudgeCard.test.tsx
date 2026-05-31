import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import NudgeCard from "../src/components/NudgeCard";
import type { Nudge } from "../src/lib/types";

const baseNudge: Nudge = {
  id: "n-1",
  rule_id: "reminder",
  category: "reminder",
  title: "Morning check-in",
  body: "How are you starting the day?",
  cta: { label: "Log now", route: "/log" },
  priority: 0.8,
  emitted_at: "2026-05-31T09:00:00Z",
};

function renderCard(overrides: Partial<Nudge> = {}, handlers = {}) {
  const onDismiss = vi.fn();
  const onSnooze = vi.fn();
  const onCtaClick = vi.fn();
  render(
    <MemoryRouter>
      <NudgeCard
        nudge={{ ...baseNudge, ...overrides }}
        onDismiss={onDismiss}
        onSnooze={onSnooze}
        onCtaClick={onCtaClick}
        {...handlers}
      />
    </MemoryRouter>
  );
  return { onDismiss, onSnooze, onCtaClick };
}

describe("NudgeCard", () => {
  it("shows title, body, and CTA link", () => {
    renderCard();
    expect(screen.getByText("Morning check-in")).toBeInTheDocument();
    expect(
      screen.getByText("How are you starting the day?")
    ).toBeInTheDocument();
    const cta = screen.getByRole("link", { name: "Log now" });
    expect(cta).toHaveAttribute("href", "/log");
  });

  it("renders without CTA when not provided", () => {
    renderCard({ cta: null });
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("calls onDismiss when Dismiss clicked", async () => {
    const user = userEvent.setup();
    const { onDismiss } = renderCard();
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("calls onSnooze when Snooze clicked", async () => {
    const user = userEvent.setup();
    const { onSnooze } = renderCard();
    await user.click(screen.getByRole("button", { name: "Snooze" }));
    expect(onSnooze).toHaveBeenCalledTimes(1);
  });

  it("uses neutral/green palette (no red urgency)", () => {
    renderCard();
    const card = screen.getByTestId("nudge-card");
    expect(card.className).not.toMatch(/\bbg-red-/);
    expect(card.className).not.toMatch(/\bborder-red-/);
  });
});
