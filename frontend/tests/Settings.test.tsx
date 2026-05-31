import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Settings from "../src/pages/Settings";

const mockGet = vi.fn();
const mockUpdate = vi.fn();

vi.mock("../src/lib/api", () => ({
  api: {
    preferences: {
      get: (...a: unknown[]) => mockGet(...a),
      update: (...a: unknown[]) => mockUpdate(...a),
    },
  },
}));

const prefs = {
  quiet_hours: { start: "21:00", end: "09:00" },
  reminder_time_override: null,
  categories_enabled: {
    reminder: true,
    missing_entry: true,
    first_insight: true,
    streak: true,
    pattern: true,
    change_point: false,
  },
};

describe("Settings page", () => {
  beforeEach(() => {
    mockGet.mockReset().mockResolvedValue(prefs);
    mockUpdate.mockReset().mockImplementation((p) => Promise.resolve(p));
  });

  it("renders preferences from API", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    await screen.findByLabelText("Quiet hours start");
    expect(
      (screen.getByLabelText("Quiet hours start") as HTMLInputElement).value
    ).toBe("21:00");
  });

  it("PUTs preferences on save", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    await screen.findByLabelText("Quiet hours start");
    await user.click(
      screen.getByRole("button", { name: "Save preferences" })
    );
    await waitFor(() => expect(mockUpdate).toHaveBeenCalledTimes(1));
  });
});
