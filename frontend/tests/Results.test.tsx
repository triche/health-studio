import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Results from "../src/pages/Results";

const mockListExerciseTypes = vi.fn();
const mockCreateExerciseType = vi.fn();
const mockDeleteExerciseType = vi.fn();
const mockListResultEntries = vi.fn();
const mockCreateResultEntry = vi.fn();
const mockUpdateResultEntry = vi.fn();
const mockDeleteResultEntry = vi.fn();
const mockGetResultTrend = vi.fn();
const mockGetPRHistory = vi.fn();

vi.mock("../src/api/results", () => ({
  listExerciseTypes: (...args: unknown[]) => mockListExerciseTypes(...args),
  createExerciseType: (...args: unknown[]) => mockCreateExerciseType(...args),
  deleteExerciseType: (...args: unknown[]) => mockDeleteExerciseType(...args),
  listResultEntries: (...args: unknown[]) => mockListResultEntries(...args),
  createResultEntry: (...args: unknown[]) => mockCreateResultEntry(...args),
  updateResultEntry: (...args: unknown[]) => mockUpdateResultEntry(...args),
  deleteResultEntry: (...args: unknown[]) => mockDeleteResultEntry(...args),
  getResultTrend: (...args: unknown[]) => mockGetResultTrend(...args),
  getPRHistory: (...args: unknown[]) => mockGetPRHistory(...args),
}));

// Mock Plotly to avoid canvas/WebGL issues in jsdom
vi.mock("react-plotly.js", () => ({
  default: (props: { data: unknown[] }) => (
    <div data-testid="plotly-chart">{JSON.stringify(props.data)}</div>
  ),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Results", () => {
  it("renders exercise type list", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
      {
        id: "2",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Back Squat (lbs)")).toBeInTheDocument();
    expect(screen.getByText("Fran (seconds)")).toBeInTheDocument();
  });

  it("shows empty state when no exercise types", async () => {
    mockListExerciseTypes.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("No exercise types. Add one to get started!"),
    ).toBeInTheDocument();
  });

  it("logs a result entry", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });
    mockCreateResultEntry.mockResolvedValue({
      id: "r1",
      exercise_type_id: "1",
      value: 225,
      display_value: null,
      recorded_date: "2025-06-01",
      is_pr: true,
      notes: null,
      created_at: "2025-06-01T00:00:00",
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("Back Squat (lbs)");

    const valueInput = screen.getByLabelText("Value");
    await user.type(valueInput, "225");
    await user.click(screen.getByText("Log"));

    await waitFor(() => {
      expect(mockCreateResultEntry).toHaveBeenCalledWith({
        exercise_type_id: "1",
        value: 225,
        recorded_date: expect.any(String),
        notes: undefined,
      });
    });
  });

  it("shows PR badge on PR entries", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 225,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
        {
          id: "r2",
          exercise_type_id: "1",
          value: 215,
          display_value: null,
          recorded_date: "2025-06-05",
          is_pr: false,
          notes: null,
          created_at: "2025-06-05T00:00:00",
        },
      ],
      total: 2,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [
        { recorded_date: "2025-06-01", value: 225, is_pr: true },
        { recorded_date: "2025-06-05", value: 215, is_pr: false },
      ],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    // PR badge should appear for the PR entry
    const prBadges = await screen.findAllByText("PR");
    expect(prBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("shows hours, minutes, seconds inputs for time-based exercises", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Fran",
      result_unit: "seconds",
      data: [],
    });
    mockCreateResultEntry.mockResolvedValue({
      id: "r1",
      exercise_type_id: "1",
      value: 323,
      display_value: null,
      recorded_date: "2025-06-01",
      is_pr: true,
      notes: null,
      created_at: "2025-06-01T00:00:00",
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("Fran (seconds)");

    // Should show h/m/s inputs instead of a single value input
    const hoursInput = screen.getByLabelText("Hours");
    const minutesInput = screen.getByLabelText("Minutes");
    const secondsInput = screen.getByLabelText("Seconds");
    expect(hoursInput).toBeInTheDocument();
    expect(minutesInput).toBeInTheDocument();
    expect(secondsInput).toBeInTheDocument();

    // 5 minutes 23 seconds = 323 seconds
    await user.type(minutesInput, "5");
    await user.type(secondsInput, "23");
    await user.click(screen.getByText("Log"));

    await waitFor(() => {
      expect(mockCreateResultEntry).toHaveBeenCalledWith({
        exercise_type_id: "1",
        value: 323,
        recorded_date: expect.any(String),
        is_rx: false,
        notes: undefined,
      });
    });
  });

  it("displays time-based entries as formatted time", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 323,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
        {
          id: "r2",
          exercise_type_id: "1",
          value: 3661,
          display_value: null,
          recorded_date: "2025-06-08",
          is_pr: false,
          notes: null,
          created_at: "2025-06-08T00:00:00",
        },
      ],
      total: 2,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Fran",
      result_unit: "seconds",
      data: [
        { recorded_date: "2025-06-01", value: 323, is_pr: true },
        { recorded_date: "2025-06-08", value: 3661, is_pr: false },
      ],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    // 323 seconds = 5m 23s
    expect(await screen.findByText("5m 23s")).toBeInTheDocument();
    // 3661 seconds = 1h 1m 1s
    expect(screen.getByText("1h 1m 1s")).toBeInTheDocument();
  });

  it("renders chart with trend data", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 225,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [
        { recorded_date: "2025-06-01", value: 225, is_pr: true },
        { recorded_date: "2025-06-08", value: 235, is_pr: true },
      ],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    // Chart should be hidden by default
    await screen.findByText("2025-06-01");
    expect(screen.queryByTestId("plotly-chart")).not.toBeInTheDocument();

    // Click the show graph toggle
    await user.click(screen.getByLabelText("Show graph"));

    await waitFor(() => {
      expect(screen.getByTestId("plotly-chart")).toBeInTheDocument();
    });
  });

  it("shows RX checkbox for crossfit_benchmark exercises", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Fran",
      result_unit: "seconds",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("Fran (seconds)");
    expect(screen.getByLabelText("RX")).toBeInTheDocument();
  });

  it("does not show RX checkbox for non-crossfit exercises", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("Back Squat (lbs)");
    expect(screen.queryByLabelText("RX")).not.toBeInTheDocument();
  });

  it("sends is_rx when logging a crossfit result with RX checked", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Fran",
      result_unit: "seconds",
      data: [],
    });
    mockCreateResultEntry.mockResolvedValue({
      id: "r1",
      exercise_type_id: "1",
      value: 323,
      display_value: null,
      recorded_date: "2025-06-01",
      is_pr: true,
      is_rx: true,
      notes: null,
      created_at: "2025-06-01T00:00:00",
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("Fran (seconds)");

    await user.type(screen.getByLabelText("Minutes"), "5");
    await user.type(screen.getByLabelText("Seconds"), "23");
    await user.click(screen.getByLabelText("RX"));
    await user.click(screen.getByText("Log"));

    await waitFor(() => {
      expect(mockCreateResultEntry).toHaveBeenCalledWith({
        exercise_type_id: "1",
        value: 323,
        recorded_date: expect.any(String),
        is_rx: true,
        notes: undefined,
      });
    });
  });

  it("shows RX badge on RX entries in the table", async () => {
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Fran",
        category: "crossfit_benchmark",
        result_unit: "seconds",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 323,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          is_rx: true,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
        {
          id: "r2",
          exercise_type_id: "1",
          value: 400,
          display_value: null,
          recorded_date: "2025-06-05",
          is_pr: false,
          is_rx: false,
          notes: null,
          created_at: "2025-06-05T00:00:00",
        },
      ],
      total: 2,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Fran",
      result_unit: "seconds",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    // Wait for entries to render
    await screen.findByText("2025-06-01");

    // Should show exactly 1 RX badge (for the RX entry)
    const rxBadges = screen.getAllByText("RX");
    // One is the checkbox label, one is the badge in the table
    const badgeElements = rxBadges.filter((el) => el.tagName === "SPAN");
    expect(badgeElements.length).toBe(1);
  });

  it("shows Edit button and enters inline edit mode on click", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 225,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          is_rx: false,
          notes: "heavy",
          created_at: "2025-06-01T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("2025-06-01");
    await user.click(screen.getByLabelText("Edit entry"));

    // Should show editable inputs pre-filled with current values
    expect(screen.getByDisplayValue("225")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2025-06-01")).toBeInTheDocument();
    expect(screen.getByDisplayValue("heavy")).toBeInTheDocument();
    // Should show Save and Cancel buttons
    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("saves edited result entry", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 225,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          is_rx: false,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });
    mockUpdateResultEntry.mockResolvedValue({
      id: "r1",
      exercise_type_id: "1",
      value: 235,
      display_value: null,
      recorded_date: "2025-06-01",
      is_pr: true,
      is_rx: false,
      notes: "new PR",
      created_at: "2025-06-01T00:00:00",
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("2025-06-01");
    await user.click(screen.getByLabelText("Edit entry"));

    const valueInput = screen.getByDisplayValue("225");
    await user.clear(valueInput);
    await user.type(valueInput, "235");

    const notesInput = screen.getByLabelText("Edit notes");
    await user.type(notesInput, "new PR");

    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockUpdateResultEntry).toHaveBeenCalledWith("r1", {
        value: 235,
        recorded_date: "2025-06-01",
        notes: "new PR",
      });
    });
  });

  it("cancels editing without saving", async () => {
    const user = userEvent.setup();
    mockListExerciseTypes.mockResolvedValue([
      {
        id: "1",
        name: "Back Squat",
        category: "power_lift",
        result_unit: "lbs",
        created_at: "2025-01-01T00:00:00",
      },
    ]);
    mockListResultEntries.mockResolvedValue({
      items: [
        {
          id: "r1",
          exercise_type_id: "1",
          value: 225,
          display_value: null,
          recorded_date: "2025-06-01",
          is_pr: true,
          is_rx: false,
          notes: null,
          created_at: "2025-06-01T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetResultTrend.mockResolvedValue({
      exercise_type_id: "1",
      exercise_name: "Back Squat",
      result_unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Results />
      </MemoryRouter>,
    );

    await screen.findByText("2025-06-01");
    await user.click(screen.getByLabelText("Edit entry"));

    // Change value
    const valueInput = screen.getByDisplayValue("225");
    await user.clear(valueInput);
    await user.type(valueInput, "999");

    // Cancel
    await user.click(screen.getByText("Cancel"));

    // Should show original value, not 999
    expect(screen.getByText("225")).toBeInTheDocument();
    expect(mockUpdateResultEntry).not.toHaveBeenCalled();
  });
});
