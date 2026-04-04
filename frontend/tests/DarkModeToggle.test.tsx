import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DarkModeToggle from "../src/components/DarkModeToggle";

beforeEach(() => {
  try {
    localStorage.clear();
  } catch {
    // jsdom may not have localStorage in all configs
  }
  document.documentElement.classList.remove("dark");
  document.documentElement.classList.remove("light");
});

describe("DarkModeToggle", () => {
  it("renders a toggle button", () => {
    render(<DarkModeToggle />);
    expect(screen.getByRole("button", { name: /toggle.*mode/i })).toBeInTheDocument();
  });

  it("defaults to dark mode", () => {
    render(<DarkModeToggle />);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("toggles to light mode on click", async () => {
    const user = userEvent.setup();
    render(<DarkModeToggle />);

    await user.click(screen.getByRole("button", { name: /toggle.*mode/i }));
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("toggles back to dark mode on second click", async () => {
    const user = userEvent.setup();
    render(<DarkModeToggle />);

    const btn = screen.getByRole("button", { name: /toggle.*mode/i });
    await user.click(btn);
    await user.click(btn);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("persists preference to localStorage", async () => {
    const user = userEvent.setup();
    render(<DarkModeToggle />);

    await user.click(screen.getByRole("button", { name: /toggle.*mode/i }));
    expect(localStorage.getItem("theme")).toBe("light");

    await user.click(screen.getByRole("button", { name: /toggle.*mode/i }));
    expect(localStorage.getItem("theme")).toBe("dark");
  });

  it("restores preference from localStorage", () => {
    localStorage.setItem("theme", "light");
    render(<DarkModeToggle />);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("calls onChange callback when toggled", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DarkModeToggle onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: /toggle.*mode/i }));
    expect(onChange).toHaveBeenCalledWith(false);
  });
});
