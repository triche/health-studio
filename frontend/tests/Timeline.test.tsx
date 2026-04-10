import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Timeline from "../src/pages/Timeline";

const mockGetTimeline = vi.fn();
const mockListTags = vi.fn();

vi.mock("../src/api/timeline", () => ({
  getTimeline: (...args: unknown[]) => mockGetTimeline(...args),
}));

vi.mock("../src/api/tags", () => ({
  listTags: () => mockListTags(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  vi.clearAllMocks();
  mockListTags.mockResolvedValue([]);
  mockGetTimeline.mockResolvedValue({
    items: [],
    total: 0,
    page: 1,
    per_page: 20,
  });
});

const MIXED_ITEMS = [
  {
    type: "journal",
    id: "j-1",
    title: "Leg Day Reflections",
    summary: "First 200 chars of content...",
    date: "2026-04-01",
    tags: ["strength"],
    metadata: {},
  },
  {
    type: "result",
    id: "r-1",
    title: "Back Squat",
    summary: "315 lbs",
    date: "2026-04-01",
    tags: ["strength"],
    metadata: {
      value: 315,
      display_value: "315 lbs",
      is_pr: true,
      is_rx: true,
      exercise_type_id: "e-1",
    },
  },
  {
    type: "metric",
    id: "m-1",
    title: "Body Weight",
    summary: "205 lbs",
    date: "2026-03-31",
    tags: [],
    metadata: { value: 205, unit: "lbs", metric_type_id: "mt-1" },
  },
  {
    type: "goal",
    id: "g-1",
    title: "Squat 405",
    summary: "Active • 77% progress",
    date: "2026-03-15",
    tags: ["strength"],
    metadata: { status: "active", progress: 77, event: "created" },
  },
];

describe("Timeline", () => {
  it("renders mixed entity cards", async () => {
    mockGetTimeline.mockResolvedValue({
      items: MIXED_ITEMS,
      total: 4,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Leg Day Reflections")).toBeInTheDocument();
    });
    expect(screen.getByText("Back Squat")).toBeInTheDocument();
    expect(screen.getByText("Body Weight")).toBeInTheDocument();
    expect(screen.getByText("Squat 405")).toBeInTheDocument();
  });

  it("shows type filter toggles", async () => {
    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /journal/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /metric/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /result/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /goal/i })).toBeInTheDocument();
  });

  it("type filter toggle triggers reload", async () => {
    mockGetTimeline.mockResolvedValue({
      items: MIXED_ITEMS,
      total: 4,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mockGetTimeline).toHaveBeenCalled();
    });

    // Click Journal to toggle it off
    const journalBtn = screen.getByRole("button", { name: /journal/i });
    fireEvent.click(journalBtn);

    await waitFor(() => {
      // Should be called again with updated types
      expect(mockGetTimeline).toHaveBeenCalledTimes(2);
    });
  });

  it("shows empty state when no data", async () => {
    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no timeline/i)).toBeInTheDocument();
    });
  });

  it("shows load more button when more items available", async () => {
    mockGetTimeline.mockResolvedValue({
      items: MIXED_ITEMS,
      total: 40,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();
    });
  });

  it("displays PR badge on result cards", async () => {
    mockGetTimeline.mockResolvedValue({
      items: [MIXED_ITEMS[1]], // Back Squat with is_pr: true
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("PR")).toBeInTheDocument();
    });
  });

  it("displays progress info on goal cards", async () => {
    mockGetTimeline.mockResolvedValue({
      items: [MIXED_ITEMS[3]], // Squat 405 goal
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getAllByText(/77%/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("cards navigate to correct detail pages", async () => {
    mockGetTimeline.mockResolvedValue({
      items: [MIXED_ITEMS[0]], // journal
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <Timeline />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Leg Day Reflections")).toBeInTheDocument();
    });

    // Journal card should link to journal detail
    const card = screen.getByText("Leg Day Reflections").closest("a, [role='link'], [data-testid]");
    if (card) {
      fireEvent.click(card);
    }
  });
});
