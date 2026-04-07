import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Backlinks from "../src/components/Backlinks";

const mockGetBacklinks = vi.fn();

vi.mock("../src/api/mentions", () => ({
  getBacklinks: (...args: unknown[]) => mockGetBacklinks(...args),
  getEntityNames: vi.fn().mockResolvedValue({ goals: [], metric_types: [], exercise_types: [] }),
  getJournalMentions: vi.fn().mockResolvedValue([]),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Backlinks", () => {
  it("shows journal entries that reference an entity", async () => {
    mockGetBacklinks.mockResolvedValue([
      {
        journal_id: "j-1",
        title: "Leg Day Thoughts",
        entry_date: "2026-04-01",
        snippet: "Working toward [[goal:Squat 405]] and felt strong",
      },
      {
        journal_id: "j-2",
        title: "Progress Update",
        entry_date: "2026-04-02",
        snippet: "Still chasing [[goal:Squat 405]]",
      },
    ]);

    render(
      <MemoryRouter>
        <Backlinks entityType="goal" entityId="g-1" />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Leg Day Thoughts")).toBeInTheDocument();
    });
    expect(screen.getByText("Progress Update")).toBeInTheDocument();
    expect(screen.getByText("2026-04-01")).toBeInTheDocument();
    expect(screen.getByText("2026-04-02")).toBeInTheDocument();
  });

  it("shows empty state when no backlinks", async () => {
    mockGetBacklinks.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Backlinks entityType="goal" entityId="g-1" />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no journal entries reference this/i)).toBeInTheDocument();
    });
  });

  it("links to journal entries", async () => {
    mockGetBacklinks.mockResolvedValue([
      {
        journal_id: "j-1",
        title: "Leg Day",
        entry_date: "2026-04-01",
        snippet: "Working on [[goal:Squat 405]]",
      },
    ]);

    render(
      <MemoryRouter>
        <Backlinks entityType="goal" entityId="g-1" />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Leg Day")).toBeInTheDocument();
    });

    const link = screen.getByText("Leg Day").closest("a");
    expect(link).toHaveAttribute("href", "/journals/j-1");
  });

  it("calls API with correct entity type and ID", async () => {
    mockGetBacklinks.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Backlinks entityType="metric_type" entityId="mt-1" />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mockGetBacklinks).toHaveBeenCalledWith("metric_type", "mt-1");
    });
  });

  it("renders section heading", async () => {
    mockGetBacklinks.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Backlinks entityType="goal" entityId="g-1" />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Referenced in Journals")).toBeInTheDocument();
    });
  });
});

describe("renderMentions", () => {
  let renderMentions: typeof import("../src/components/MentionRenderer").renderMentions;

  beforeEach(async () => {
    const mod = await import("../src/components/MentionRenderer");
    renderMentions = mod.renderMentions;
  });

  it("renders [[Results:Name]] as a link", () => {
    const nodes = renderMentions("Did [[Results:Strict Pull Up]] today");
    const { container } = render(<MemoryRouter>{nodes}</MemoryRouter>);
    const link = container.querySelector("a");
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain("Strict Pull Up");
    expect(link?.getAttribute("href")).toBe("/results");
  });

  it("renders [[Goals:Name]] as a link", () => {
    const nodes = renderMentions("Working on [[Goals:Squat 405]]");
    const { container } = render(<MemoryRouter>{nodes}</MemoryRouter>);
    const link = container.querySelector("a");
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain("Squat 405");
    expect(link?.getAttribute("href")).toBe("/goals");
  });

  it("renders [[Metrics:Name]] as a link", () => {
    const nodes = renderMentions("Tracked [[Metrics:Body Weight]]");
    const { container } = render(<MemoryRouter>{nodes}</MemoryRouter>);
    const link = container.querySelector("a");
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain("Body Weight");
    expect(link?.getAttribute("href")).toBe("/metrics");
  });

  it("handles mixed case aliases", () => {
    const nodes = renderMentions("[[GOAL:A]] and [[exercise:B]] and [[results:C]]");
    const { container } = render(<MemoryRouter>{nodes}</MemoryRouter>);
    const links = container.querySelectorAll("a");
    expect(links.length).toBe(3);
  });
});
