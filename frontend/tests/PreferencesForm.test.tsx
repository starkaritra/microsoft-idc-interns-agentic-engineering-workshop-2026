import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PreferencesForm from "../src/components/PreferencesForm";
import type { Preferences } from "../src/lib/types";

const initial: Preferences = {
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

describe("PreferencesForm", () => {
  let onSave: ReturnType<typeof vi.fn> & ((p: Preferences) => Promise<void>);

  beforeEach(() => {
    onSave = vi.fn().mockResolvedValue(undefined) as typeof onSave;
  });

  it("prefills quiet hours from initial", () => {
    render(<PreferencesForm initial={initial} onSave={onSave} />);
    expect(
      (screen.getByLabelText("Quiet hours start") as HTMLInputElement).value
    ).toBe("21:00");
    expect(
      (screen.getByLabelText("Quiet hours end") as HTMLInputElement).value
    ).toBe("09:00");
  });

  it("reflects category toggle state", () => {
    render(<PreferencesForm initial={initial} onSave={onSave} />);
    expect(
      (screen.getByLabelText("Daily reminder") as HTMLInputElement).checked
    ).toBe(true);
    expect(
      (screen.getByLabelText("Reflection prompt") as HTMLInputElement).checked
    ).toBe(false);
  });

  it("saves merged payload and shows confirmation", async () => {
    const user = userEvent.setup();
    render(<PreferencesForm initial={initial} onSave={onSave} />);
    await user.click(screen.getByLabelText("Reflection prompt"));
    await user.click(
      screen.getByRole("button", { name: "Save preferences" })
    );
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    const payload = onSave.mock.calls[0][0] as Preferences;
    expect(payload.categories_enabled.change_point).toBe(true);
    expect(payload.quiet_hours).toEqual({ start: "21:00", end: "09:00" });
    expect(await screen.findByRole("status")).toHaveTextContent("Saved");
  });

  it("rejects invalid quiet hours (start == end)", async () => {
    const user = userEvent.setup();
    render(<PreferencesForm initial={initial} onSave={onSave} />);
    const end = screen.getByLabelText("Quiet hours end") as HTMLInputElement;
    await user.clear(end);
    await user.type(end, "21:00");
    const saveBtn = screen.getByRole("button", {
      name: "Save preferences",
    }) as HTMLButtonElement;
    expect(saveBtn).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent(
      /start and end must be different/i
    );
    await user.click(saveBtn);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("disable-all turns every category off", async () => {
    const user = userEvent.setup();
    render(<PreferencesForm initial={initial} onSave={onSave} />);
    await user.click(
      screen.getByRole("button", { name: "Disable all nudges" })
    );
    expect(
      (screen.getByLabelText("Daily reminder") as HTMLInputElement).checked
    ).toBe(false);
    expect(
      (screen.getByLabelText("Pattern discovery") as HTMLInputElement).checked
    ).toBe(false);
  });
});
