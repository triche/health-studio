import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Sidebar from "../src/components/Sidebar";

beforeEach(() => {
  try {
    localStorage.clear();
  } catch {
    // jsdom may not have localStorage in all configs
  }
  document.documentElement.classList.add("dark");
});

describe("Sidebar responsive behavior", () => {
  it("renders the hamburger menu button for mobile", () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    // Hamburger button should exist (visible on mobile via CSS)
    expect(screen.getByRole("button", { name: /open menu/i })).toBeInTheDocument();
  });

  it("renders sidebar links", () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Journal")).toBeInTheDocument();
    expect(screen.getByText("Metrics")).toBeInTheDocument();
    expect(screen.getByText("Results")).toBeInTheDocument();
    expect(screen.getByText("Goals")).toBeInTheDocument();
  });

  it("toggles mobile menu open and closed", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    // Open menu
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    // The overlay should appear
    expect(screen.getByTestId("sidebar-overlay")).toBeInTheDocument();

    // Close via close button
    await user.click(screen.getByRole("button", { name: /close menu/i }));
    expect(screen.queryByTestId("sidebar-overlay")).not.toBeInTheDocument();
  });

  it("closes mobile menu when a nav link is clicked", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getByTestId("sidebar-overlay")).toBeInTheDocument();

    // Click a link in the mobile drawer (multiple "Journal" links exist — desktop + mobile)
    const journalLinks = screen.getAllByText("Journal");
    await user.click(journalLinks[journalLinks.length - 1]);
    expect(screen.queryByTestId("sidebar-overlay")).not.toBeInTheDocument();
  });

  it("renders the dark mode toggle", () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /toggle.*mode/i })).toBeInTheDocument();
  });

  it("renders icon buttons for settings, dark mode, and logout", () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={() => {}} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /toggle.*mode/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });
});
