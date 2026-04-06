import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Goals from "../src/pages/Goals";

const mockListGoals = vi.fn();
const mockCreateGoal = vi.fn();
const mockUpdateGoal = vi.fn();
const mockDeleteGoal = vi.fn();

vi.mock("../src/api/goals", () => ({
  listGoals: (...args: unknown[]) => mockListGoals(...args),
  createGoal: (...args: unknown[]) => mockCreateGoal(...args),
  updateGoal: (...args: unknown[]) => mockUpdateGoal(...args),
  deleteGoal: (...args: unknown[]) => mockDeleteGoal(...args),
}));

const mockListMetricTypes = vi.fn();
vi.mock("../src/api/metrics", () => ({
  listMetricTypes: (...args: unknown[]) => mockListMetricTypes(...args),
  listMetricEntries: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  createMetricType: vi.fn(),
  deleteMetricType: vi.fn(),
  createMetricEntry: vi.fn(),
  updateMetricEntry: vi.fn(),
  deleteMetricEntry: vi.fn(),
  getMetricTrend: vi.fn(),
}));

const mockListExerciseTypes = vi.fn();
vi.mock("../src/api/results", () => ({
  listExerciseTypes: (...args: unknown[]) => mockListExerciseTypes(...args),
  listResultEntries: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  createExerciseType: vi.fn(),
  deleteExerciseType: vi.fn(),
  createResultEntry: vi.fn(),
  updateResultEntry: vi.fn(),
  deleteResultEntry: vi.fn(),
  getResultTrend: vi.fn(),
  getPRHistory: vi.fn(),
}));

// Mock react-md-editor to avoid complex rendering in tests
vi.mock("@uiw/react-md-editor", () => {
  const commands = {
    bold: { name: "bold" },
    italic: { name: "italic" },
    strikethrough: { name: "strikethrough" },
    title1: { name: "title1" },
    title2: { name: "title2" },
    title3: { name: "title3" },
    title4: { name: "title4" },
    quote: { name: "quote" },
    unorderedListCommand: { name: "unordered-list" },
    orderedListCommand: { name: "ordered-list" },
    checkedListCommand: { name: "checked-list" },
    link: { name: "link" },
    image: { name: "image" },
    hr: { name: "hr" },
    divider: { name: "divider" },
    group: () => ({ name: "group" }),
  };
  return {
    default: ({
      value,
      onChange,
      "data-testid": testId,
    }: {
      value: string;
      onChange: (v: string) => void;
      "data-testid"?: string;
    }) => (
      <textarea
        data-testid={testId || "md-editor"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    ),
    commands,
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  mockListMetricTypes.mockResolvedValue([
    { id: "mt-1", name: "Weight", unit: "lbs", created_at: "2025-01-01T00:00:00" },
    { id: "mt-2", name: "Sleep", unit: "minutes", created_at: "2025-01-01T00:00:00" },
  ]);
  mockListExerciseTypes.mockResolvedValue([
    {
      id: "et-1",
      name: "Back Squat",
      category: "power_lift",
      result_unit: "lbs",
      created_at: "2025-01-01T00:00:00",
    },
    {
      id: "et-2",
      name: "Fran",
      category: "crossfit_benchmark",
      result_unit: "seconds",
      created_at: "2025-01-01T00:00:00",
    },
  ]);
});

const GOAL_ITEM = {
  id: "g-1",
  title: "Lose Weight",
  description: "Get to 180 lbs",
  plan: "## Plan\n- Eat less",
  target_type: "metric",
  target_id: "mt-1",
  target_value: 180,
  start_value: null,
  current_value: 190,
  lower_is_better: false,
  status: "active",
  deadline: "2025-12-31",
  progress: 50,
  created_at: "2025-01-01T00:00:00",
  updated_at: "2025-01-01T00:00:00",
};

describe("Goals", () => {
  it("renders goals list", async () => {
    mockListGoals.mockResolvedValue({
      items: [GOAL_ITEM],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Lose Weight")).toBeInTheDocument();
  });

  it("shows empty state when no goals", async () => {
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/no goals/i)).toBeInTheDocument();
  });

  it("displays progress bar with correct percentage", async () => {
    mockListGoals.mockResolvedValue({
      items: [{ ...GOAL_ITEM, progress: 75 }],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText("75%")).toBeInTheDocument();
  });

  it("creates a new goal", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    mockCreateGoal.mockResolvedValue({
      ...GOAL_ITEM,
      id: "g-new",
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);

    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.type(screen.getByLabelText(/title/i), "Lose Weight");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "mt-1");
    await user.type(screen.getByLabelText(/target value/i), "180");

    // Re-mock to include new goal on next load
    mockListGoals.mockResolvedValue({
      items: [GOAL_ITEM],
      total: 1,
      page: 1,
      per_page: 20,
    });

    await user.click(screen.getByRole("button", { name: /save goal/i }));

    await waitFor(() => {
      expect(mockCreateGoal).toHaveBeenCalled();
    });
  });

  it("can update goal status to completed", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({
      items: [GOAL_ITEM],
      total: 1,
      page: 1,
      per_page: 20,
    });
    mockUpdateGoal.mockResolvedValue({ ...GOAL_ITEM, status: "completed" });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText("Lose Weight");
    await user.click(screen.getByRole("button", { name: /complete/i }));

    await waitFor(() => {
      expect(mockUpdateGoal).toHaveBeenCalledWith("g-1", { status: "completed" });
    });
  });

  it("can delete a goal", async () => {
    const user = userEvent.setup();
    mockListGoals
      .mockResolvedValueOnce({
        items: [GOAL_ITEM],
        total: 1,
        page: 1,
        per_page: 20,
      })
      .mockResolvedValueOnce({ items: [], total: 0, page: 1, per_page: 20 });
    mockDeleteGoal.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText("Lose Weight");
    await user.click(screen.getByRole("button", { name: /delete/i }));

    await waitFor(() => {
      expect(mockDeleteGoal).toHaveBeenCalledWith("g-1");
    });
  });

  it("filters goals by status", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({
      items: [GOAL_ITEM],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText("Lose Weight");

    const select = screen.getByLabelText(/filter/i);
    await user.selectOptions(select, "completed");

    await waitFor(() => {
      expect(mockListGoals).toHaveBeenCalledWith(expect.objectContaining({ status: "completed" }));
    });
  });

  it("shows direction indicator for lower-is-better goals", async () => {
    mockListGoals.mockResolvedValue({
      items: [{ ...GOAL_ITEM, lower_is_better: true }],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/↓ lower is better/i)).toBeInTheDocument();
  });

  it("shows direction indicator for higher-is-better goals", async () => {
    mockListGoals.mockResolvedValue({
      items: [{ ...GOAL_ITEM, lower_is_better: false }],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/↑ higher is better/i)).toBeInTheDocument();
  });

  it("includes lower_is_better when creating a goal with checkbox checked", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    mockCreateGoal.mockResolvedValue({ ...GOAL_ITEM, id: "g-new", lower_is_better: true });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.type(screen.getByLabelText(/title/i), "Lose Weight");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "mt-1");
    await user.type(screen.getByLabelText(/target value/i), "180");
    await user.click(screen.getByLabelText(/lower is better/i));

    mockListGoals.mockResolvedValue({ items: [GOAL_ITEM], total: 1, page: 1, per_page: 20 });
    await user.click(screen.getByRole("button", { name: /save goal/i }));

    await waitFor(() => {
      expect(mockCreateGoal).toHaveBeenCalledWith(
        expect.objectContaining({ lower_is_better: true }),
      );
    });
  });

  it("shows start value in goal details when set", async () => {
    mockListGoals.mockResolvedValue({
      items: [{ ...GOAL_ITEM, start_value: 253, lower_is_better: true }],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/start: 253/i)).toBeInTheDocument();
  });

  it("includes start_value when creating a goal", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    mockCreateGoal.mockResolvedValue({ ...GOAL_ITEM, id: "g-new", start_value: 253 });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.type(screen.getByLabelText(/title/i), "Lose Weight");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "mt-1");
    await user.type(screen.getByLabelText(/target value/i), "240");
    await user.type(screen.getByLabelText(/starting value/i), "253");

    mockListGoals.mockResolvedValue({ items: [GOAL_ITEM], total: 1, page: 1, per_page: 20 });
    await user.click(screen.getByRole("button", { name: /save goal/i }));

    await waitFor(() => {
      expect(mockCreateGoal).toHaveBeenCalledWith(expect.objectContaining({ start_value: 253 }));
    });
  });

  it("formats time values for exercise/seconds goals in display", async () => {
    mockListGoals.mockResolvedValue({
      items: [
        {
          ...GOAL_ITEM,
          title: "Beat Fran",
          target_type: "result",
          target_id: "et-2",
          target_value: 180,
          current_value: 245,
          start_value: 300,
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    // target_value 180s = 3m 0s → shown in target info and progress bar
    // current_value 245s = 4m 5s, start_value 300s = 5m 0s
    expect(await screen.findByText(/4m 5s \/ 3m/)).toBeInTheDocument();
    expect(screen.getByText(/start: 5m/i)).toBeInTheDocument();
  });

  it("formats duration values for metric/minutes goals in display", async () => {
    mockListGoals.mockResolvedValue({
      items: [
        {
          ...GOAL_ITEM,
          title: "Sleep More",
          target_type: "metric",
          target_id: "mt-2",
          target_value: 480,
          current_value: 420,
          start_value: 360,
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    // current/target in progress bar: 7h 0m / 8h 0m
    expect(await screen.findByText(/7h 0m \/ 8h 0m/)).toBeInTheDocument();
    expect(screen.getByText(/start: 6h 0m/i)).toBeInTheDocument();
  });

  it("shows h/m/s inputs for target value when exercise type uses seconds", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.selectOptions(screen.getByLabelText(/target type/i), "result");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "et-2");

    expect(screen.getByLabelText(/target hours/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target minutes/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target seconds/i)).toBeInTheDocument();
  });

  it("shows h/m inputs for target value when metric type uses minutes", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    // target type defaults to "metric"
    await user.selectOptions(screen.getByLabelText(/^target$/i), "mt-2");

    expect(screen.getByLabelText(/target hours/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target minutes/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/target seconds/i)).not.toBeInTheDocument();
  });

  it("submits time goal with converted seconds value", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    mockCreateGoal.mockResolvedValue({ ...GOAL_ITEM, id: "g-new" });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.type(screen.getByLabelText(/title/i), "Beat Fran");
    await user.selectOptions(screen.getByLabelText(/target type/i), "result");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "et-2");
    await user.type(screen.getByLabelText(/target hours/i), "0");
    await user.type(screen.getByLabelText(/target minutes/i), "3");
    await user.type(screen.getByLabelText(/target seconds/i), "30");

    mockListGoals.mockResolvedValue({ items: [GOAL_ITEM], total: 1, page: 1, per_page: 20 });
    await user.click(screen.getByRole("button", { name: /save goal/i }));

    await waitFor(() => {
      // 0*3600 + 3*60 + 30 = 210 seconds
      expect(mockCreateGoal).toHaveBeenCalledWith(expect.objectContaining({ target_value: 210 }));
    });
  });

  it("submits duration goal with converted minutes value", async () => {
    const user = userEvent.setup();
    mockListGoals.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    mockCreateGoal.mockResolvedValue({ ...GOAL_ITEM, id: "g-new" });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText(/no goals/i);
    await user.click(screen.getByRole("button", { name: /new goal/i }));
    await user.type(screen.getByLabelText(/title/i), "Sleep More");
    await user.selectOptions(screen.getByLabelText(/^target$/i), "mt-2");
    await user.type(screen.getByLabelText(/target hours/i), "8");
    await user.type(screen.getByLabelText(/target minutes/i), "0");

    mockListGoals.mockResolvedValue({ items: [GOAL_ITEM], total: 1, page: 1, per_page: 20 });
    await user.click(screen.getByRole("button", { name: /save goal/i }));

    await waitFor(() => {
      // 8*60 + 0 = 480 minutes
      expect(mockCreateGoal).toHaveBeenCalledWith(expect.objectContaining({ target_value: 480 }));
    });
  });

  it("populates time fields when editing a time-based goal", async () => {
    const user = userEvent.setup();
    const timeGoal = {
      ...GOAL_ITEM,
      title: "Beat Fran",
      target_type: "result",
      target_id: "et-2",
      target_value: 210,
      start_value: 300,
      current_value: 245,
    };
    mockListGoals.mockResolvedValue({
      items: [timeGoal],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Goals />
      </MemoryRouter>,
    );

    await screen.findByText("Beat Fran");
    await user.click(screen.getByRole("button", { name: /edit/i }));

    // 210 seconds = 0h, 3m, 30s
    expect(screen.getByLabelText(/target hours/i)).toHaveValue(0);
    expect(screen.getByLabelText(/target minutes/i)).toHaveValue(3);
    expect(screen.getByLabelText(/target seconds/i)).toHaveValue(30);

    // 300 seconds = 0h, 5m, 0s
    expect(screen.getByLabelText(/start hours/i)).toHaveValue(0);
    expect(screen.getByLabelText(/start minutes/i)).toHaveValue(5);
    expect(screen.getByLabelText(/start seconds/i)).toHaveValue(0);
  });
});
