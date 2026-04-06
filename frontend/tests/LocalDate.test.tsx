import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock all API modules used by the pages
const mockListMetricTypes = vi.fn();
const mockListMetricEntries = vi.fn();
const mockGetMetricTrend = vi.fn();

vi.mock("../src/api/metrics", () => ({
  listMetricTypes: (...args: unknown[]) => mockListMetricTypes(...args),
  createMetricType: vi.fn(),
  deleteMetricType: vi.fn(),
  listMetricEntries: (...args: unknown[]) => mockListMetricEntries(...args),
  createMetricEntry: vi.fn(),
  updateMetricEntry: vi.fn(),
  deleteMetricEntry: vi.fn(),
  getMetricTrend: (...args: unknown[]) => mockGetMetricTrend(...args),
}));

const mockListExerciseTypes = vi.fn();
const mockListResultEntries = vi.fn();
const mockGetResultTrend = vi.fn();

vi.mock("../src/api/results", () => ({
  listExerciseTypes: (...args: unknown[]) => mockListExerciseTypes(...args),
  createExerciseType: vi.fn(),
  deleteExerciseType: vi.fn(),
  listResultEntries: (...args: unknown[]) => mockListResultEntries(...args),
  createResultEntry: vi.fn(),
  updateResultEntry: vi.fn(),
  deleteResultEntry: vi.fn(),
  getResultTrend: (...args: unknown[]) => mockGetResultTrend(...args),
}));

vi.mock("../src/api/journals", () => ({
  getJournal: vi.fn(),
  createJournal: vi.fn(),
  updateJournal: vi.fn(),
}));

vi.mock("react-plotly.js", () => ({
  default: () => <div data-testid="plotly-chart" />,
}));

declare const process: { env: Record<string, string | undefined> };
const originalTZ = process.env.TZ;

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
  process.env.TZ = originalTZ;
});

describe("Date defaults use local time, not UTC", () => {
  // Simulate 11 PM CDT on April 5 = 4 AM UTC on April 6
  // If the code uses toISOString(), it would incorrectly show 2026-04-06
  // Correct behavior: show 2026-04-05 (the local date)
  const LOCAL_DATE = "2026-04-05";
  const UTC_DATE = "2026-04-06";

  function mockLateNightCentral() {
    // Set timezone to Central so getDate()/getMonth()/getFullYear() use CDT
    process.env.TZ = "America/Chicago";
    // April 6, 2026 04:00:00 UTC = April 5, 2026 11:00:00 PM CDT
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-04-06T04:00:00Z"));

    // Provide a type so the entry form (with date input) renders
    mockListMetricTypes.mockResolvedValue([
      { id: "t1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "t1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });

    mockListExerciseTypes.mockResolvedValue([
      {
        id: "t1",
        name: "Back Squat",
        category: "barbell",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "t1",
      exercise_name: "Back Squat",
      unit: "lbs",
      data: [],
    });
  }

  it("Metrics page defaults date to local date, not UTC", async () => {
    mockLateNightCentral();
    const { default: Metrics } = await import("../src/pages/Metrics");
    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue(LOCAL_DATE)).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue(UTC_DATE)).toBeNull();
  });

  it("Results page defaults date to local date, not UTC", async () => {
    mockLateNightCentral();
    const { default: Results } = await import("../src/pages/Results");
    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue(LOCAL_DATE)).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue(UTC_DATE)).toBeNull();
  });

  it("JournalEdit page defaults date to local date, not UTC", async () => {
    mockLateNightCentral();
    const { default: JournalEdit } = await import("../src/pages/JournalEdit");
    render(
      <MemoryRouter initialEntries={["/journal/new"]}>
        <JournalEdit />
      </MemoryRouter>,
    );
    const dateInput = screen.getByDisplayValue(LOCAL_DATE);
    expect(dateInput).toBeInTheDocument();
    expect(screen.queryByDisplayValue(UTC_DATE)).toBeNull();
  });
});
