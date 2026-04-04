import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Metrics from "../src/pages/Metrics";

const mockListMetricTypes = vi.fn();
const mockCreateMetricType = vi.fn();
const mockDeleteMetricType = vi.fn();
const mockListMetricEntries = vi.fn();
const mockCreateMetricEntry = vi.fn();
const mockUpdateMetricEntry = vi.fn();
const mockDeleteMetricEntry = vi.fn();
const mockGetMetricTrend = vi.fn();

vi.mock("../src/api/metrics", () => ({
  listMetricTypes: (...args: unknown[]) => mockListMetricTypes(...args),
  createMetricType: (...args: unknown[]) => mockCreateMetricType(...args),
  deleteMetricType: (...args: unknown[]) => mockDeleteMetricType(...args),
  listMetricEntries: (...args: unknown[]) => mockListMetricEntries(...args),
  createMetricEntry: (...args: unknown[]) => mockCreateMetricEntry(...args),
  updateMetricEntry: (...args: unknown[]) => mockUpdateMetricEntry(...args),
  deleteMetricEntry: (...args: unknown[]) => mockDeleteMetricEntry(...args),
  getMetricTrend: (...args: unknown[]) => mockGetMetricTrend(...args),
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

describe("Metrics", () => {
  it("renders metric type list", async () => {
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
      { id: "2", name: "Steps", unit: "count", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Weight (lbs)")).toBeInTheDocument();
    expect(screen.getByText("Steps (count)")).toBeInTheDocument();
  });

  it("shows empty state when no metric types", async () => {
    mockListMetricTypes.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    expect(await screen.findByText("No metric types. Add one to get started!")).toBeInTheDocument();
  });

  it("logs a metric entry", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });
    mockCreateMetricEntry.mockResolvedValue({
      id: "e1",
      metric_type_id: "1",
      value: 185,
      recorded_date: "2025-01-15",
      notes: null,
      created_at: "2025-01-15T00:00:00",
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    await screen.findByText("Weight (lbs)");

    const valueInput = screen.getByLabelText("Value");
    await user.type(valueInput, "185");
    await user.click(screen.getByText("Log"));

    await waitFor(() => {
      expect(mockCreateMetricEntry).toHaveBeenCalledWith({
        metric_type_id: "1",
        value: 185,
        recorded_date: expect.any(String),
        notes: undefined,
      });
    });
  });

  it("renders chart with trend data", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [
        {
          id: "e1",
          metric_type_id: "1",
          value: 185,
          recorded_date: "2025-01-15",
          notes: null,
          created_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [
        { recorded_date: "2025-01-10", value: 186 },
        { recorded_date: "2025-01-15", value: 185 },
      ],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    // Chart hidden by default
    await screen.findByText("Weight (lbs)");
    expect(screen.queryByTestId("plotly-chart")).not.toBeInTheDocument();

    // Click the show graph toggle
    await user.click(screen.getByLabelText("Show graph"));

    await waitFor(() => {
      expect(screen.getByTestId("plotly-chart")).toBeInTheDocument();
    });
  });

  it("shows 7-day average toggle and adds trace when enabled", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [
        { recorded_date: "2025-01-10", value: 186 },
        { recorded_date: "2025-01-12", value: 184 },
        { recorded_date: "2025-01-15", value: 185 },
      ],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    // Show the graph first
    await screen.findByText("Weight (lbs)");
    await user.click(screen.getByLabelText("Show graph"));

    await waitFor(() => {
      expect(screen.getByTestId("plotly-chart")).toBeInTheDocument();
    });

    const toggle = screen.getByLabelText("7-day average");
    expect(toggle).toBeInTheDocument();
    expect(toggle).not.toBeChecked();

    // Chart should have 1 trace (raw data only)
    const chartBefore = screen.getByTestId("plotly-chart");
    const dataBefore = JSON.parse(chartBefore.textContent!);
    expect(dataBefore).toHaveLength(1);

    // Enable the toggle
    await user.click(toggle);
    expect(toggle).toBeChecked();

    // Chart should now have 2 traces (raw + average)
    const chartAfter = screen.getByTestId("plotly-chart");
    const dataAfter = JSON.parse(chartAfter.textContent!);
    expect(dataAfter).toHaveLength(2);
    expect(dataAfter[1].name).toBe("7-day avg");
  });

  it("shows hours and minutes inputs for duration metrics", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Sleep Duration", unit: "minutes", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Sleep Duration",
      unit: "minutes",
      data: [],
    });
    mockCreateMetricEntry.mockResolvedValue({
      id: "e1",
      metric_type_id: "1",
      value: 450,
      recorded_date: "2025-01-15",
      notes: null,
      created_at: "2025-01-15T00:00:00",
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    await screen.findByText("Sleep Duration (minutes)");

    // Should show hours and minutes inputs instead of a single value input
    const hoursInput = screen.getByLabelText("Hours");
    const minutesInput = screen.getByLabelText("Minutes");
    expect(hoursInput).toBeInTheDocument();
    expect(minutesInput).toBeInTheDocument();

    await user.type(hoursInput, "7");
    await user.type(minutesInput, "30");
    await user.click(screen.getByText("Log"));

    await waitFor(() => {
      expect(mockCreateMetricEntry).toHaveBeenCalledWith({
        metric_type_id: "1",
        value: 450,
        recorded_date: expect.any(String),
        notes: undefined,
      });
    });
  });

  it("displays duration entries as hours and minutes", async () => {
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Sleep Duration", unit: "minutes", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [
        {
          id: "e1",
          metric_type_id: "1",
          value: 450,
          recorded_date: "2025-01-15",
          notes: null,
          created_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Sleep Duration",
      unit: "minutes",
      data: [{ recorded_date: "2025-01-15", value: 450 }],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    // 450 minutes = 7h 30m
    expect(await screen.findByText("7h 30m")).toBeInTheDocument();
  });

  it("shows Edit button and enters inline edit mode on click", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [
        {
          id: "e1",
          metric_type_id: "1",
          value: 185,
          recorded_date: "2025-01-15",
          notes: "morning",
          created_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    await screen.findByText("2025-01-15");
    await user.click(screen.getByLabelText("Edit entry"));

    expect(screen.getByDisplayValue("185")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2025-01-15")).toBeInTheDocument();
    expect(screen.getByDisplayValue("morning")).toBeInTheDocument();
    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("saves edited metric entry", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [
        {
          id: "e1",
          metric_type_id: "1",
          value: 185,
          recorded_date: "2025-01-15",
          notes: null,
          created_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });
    mockUpdateMetricEntry.mockResolvedValue({
      id: "e1",
      metric_type_id: "1",
      value: 183,
      recorded_date: "2025-01-15",
      notes: "after run",
      created_at: "2025-01-15T00:00:00",
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    await screen.findByText("2025-01-15");
    await user.click(screen.getByLabelText("Edit entry"));

    const valueInput = screen.getByDisplayValue("185");
    await user.clear(valueInput);
    await user.type(valueInput, "183");

    const notesInput = screen.getByLabelText("Edit notes");
    await user.type(notesInput, "after run");

    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockUpdateMetricEntry).toHaveBeenCalledWith("e1", {
        value: 183,
        recorded_date: "2025-01-15",
        notes: "after run",
      });
    });
  });

  it("cancels editing without saving", async () => {
    const user = userEvent.setup();
    mockListMetricTypes.mockResolvedValue([
      { id: "1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    ]);
    mockListMetricEntries.mockResolvedValue({
      items: [
        {
          id: "e1",
          metric_type_id: "1",
          value: 185,
          recorded_date: "2025-01-15",
          notes: null,
          created_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 50,
    });
    mockGetMetricTrend.mockResolvedValue({
      metric_type_id: "1",
      metric_name: "Weight",
      unit: "lbs",
      data: [],
    });

    render(
      <MemoryRouter>
        <Metrics />
      </MemoryRouter>,
    );

    await screen.findByText("2025-01-15");
    await user.click(screen.getByLabelText("Edit entry"));

    const valueInput = screen.getByDisplayValue("185");
    await user.clear(valueInput);
    await user.type(valueInput, "999");

    await user.click(screen.getByText("Cancel"));

    expect(screen.getByText("185")).toBeInTheDocument();
    expect(mockUpdateMetricEntry).not.toHaveBeenCalled();
  });
});
