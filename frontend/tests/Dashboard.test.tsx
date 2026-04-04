import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "../src/pages/Dashboard";

const mockGetDashboardSummary = vi.fn();

vi.mock("../src/api/dashboard", () => ({
  getDashboardSummary: (...args: unknown[]) => mockGetDashboardSummary(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

const SUMMARY = {
  recent_journals: [
    { id: "j-1", title: "Morning Thoughts", entry_date: "2025-01-15" },
    { id: "j-2", title: "Workout Log", entry_date: "2025-01-14" },
  ],
  active_goals: [
    {
      id: "g-1",
      title: "Lose Weight",
      target_type: "metric",
      target_value: 180,
      current_value: 190,
      progress: 50,
      status: "active",
      deadline: "2025-12-31",
    },
  ],
  latest_metrics: [
    {
      metric_type_id: "mt-1",
      metric_name: "Weight",
      unit: "lbs",
      value: 190,
      recorded_date: "2025-01-15",
    },
  ],
  recent_prs: [
    {
      id: "pr-1",
      exercise_name: "Back Squat",
      value: 250,
      display_value: null,
      recorded_date: "2025-01-15",
      is_rx: false,
    },
  ],
};

describe("Dashboard", () => {
  it("renders summary cards", async () => {
    mockGetDashboardSummary.mockResolvedValue(SUMMARY);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Morning Thoughts")).toBeInTheDocument();
    expect(screen.getByText("Workout Log")).toBeInTheDocument();
    expect(screen.getByText("Lose Weight")).toBeInTheDocument();
    expect(screen.getByText(/190/)).toBeInTheDocument();
    expect(screen.getByText("Back Squat")).toBeInTheDocument();
  });

  it("displays goal progress bar with correct percentage", async () => {
    mockGetDashboardSummary.mockResolvedValue(SUMMARY);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(await screen.findByText("50%")).toBeInTheDocument();
  });

  it("shows empty state when no data", async () => {
    mockGetDashboardSummary.mockResolvedValue({
      recent_journals: [],
      active_goals: [],
      latest_metrics: [],
      recent_prs: [],
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/no recent journal entries/i)).toBeInTheDocument();
  });

  it("displays PR badge for recent PRs", async () => {
    mockGetDashboardSummary.mockResolvedValue(SUMMARY);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Back Squat")).toBeInTheDocument();
    expect(screen.getByText("250")).toBeInTheDocument();
  });
});
