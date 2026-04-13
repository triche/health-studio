import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Graph from "../src/pages/Graph";

const mockGetGraph = vi.fn();

vi.mock("../src/api/graph", () => ({
  getGraph: (...args: unknown[]) => mockGetGraph(...args),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

// Mock react-force-graph-2d as a simple div since canvas doesn't work in jsdom
vi.mock("react-force-graph-2d", () => ({
  default: vi.fn(
    ({
      graphData,
      onNodeClick,
    }: {
      graphData: { nodes: { id: string }[] };
      onNodeClick?: (node: { id: string }) => void;
    }) => (
      <div data-testid="force-graph">
        {graphData.nodes.map((n: { id: string }) => (
          <div key={n.id} data-testid={`graph-node-${n.id}`} onClick={() => onNodeClick?.(n)}>
            {n.id}
          </div>
        ))}
      </div>
    ),
  ),
}));

const SAMPLE_GRAPH = {
  nodes: [
    {
      id: "journal:j-1",
      type: "journal",
      label: "Leg Day Reflections",
      date: "2026-04-01",
      tags: ["strength"],
    },
    {
      id: "goal:g-1",
      type: "goal",
      label: "Squat 405",
      status: "active",
      progress: 77,
      tags: ["strength"],
    },
    { id: "exercise_type:e-1", type: "exercise_type", label: "Back Squat", tags: ["strength"] },
    { id: "metric_type:m-1", type: "metric_type", label: "Body Weight", tags: [] },
  ],
  edges: [
    { source: "journal:j-1", target: "goal:g-1", type: "mentions" },
    { source: "journal:j-1", target: "exercise_type:e-1", type: "mentions" },
    { source: "goal:g-1", target: "exercise_type:e-1", type: "tracks" },
    { source: "journal:j-1", target: "goal:g-1", type: "shared_tag", tag: "strength" },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockGetGraph.mockResolvedValue(SAMPLE_GRAPH);
});

describe("Graph", () => {
  it("renders graph page without errors", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("force-graph")).toBeInTheDocument();
    });
  });

  it("loads graph data on mount", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mockGetGraph).toHaveBeenCalledTimes(1);
    });
  });

  it("node count matches expected entities", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("graph-node-journal:j-1")).toBeInTheDocument();
    });
    expect(screen.getByTestId("graph-node-goal:g-1")).toBeInTheDocument();
    expect(screen.getByTestId("graph-node-exercise_type:e-1")).toBeInTheDocument();
    expect(screen.getByTestId("graph-node-metric_type:m-1")).toBeInTheDocument();
  });

  it("clicking node shows detail panel", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("graph-node-journal:j-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("graph-node-journal:j-1"));

    await waitFor(() => {
      expect(screen.getByText("Leg Day Reflections")).toBeInTheDocument();
    });
  });

  it("shows type filter toggles", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /journal/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /goal/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /metric/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /exercise/i })).toBeInTheDocument();
  });

  it("type filter toggles filter nodes", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("graph-node-journal:j-1")).toBeInTheDocument();
    });

    // Toggle journal off
    const journalBtn = screen.getByRole("button", { name: /journal/i });
    fireEvent.click(journalBtn);

    await waitFor(() => {
      expect(screen.queryByTestId("graph-node-journal:j-1")).not.toBeInTheDocument();
    });
  });

  it("shows empty state when no data", async () => {
    mockGetGraph.mockResolvedValue({ nodes: [], edges: [] });

    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no data/i)).toBeInTheDocument();
    });
  });

  it("double-click navigates to entity detail", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("graph-node-journal:j-1")).toBeInTheDocument();
    });

    // Simulate double-click via two rapid clicks
    const node = screen.getByTestId("graph-node-journal:j-1");
    fireEvent.click(node);
    fireEvent.click(node);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/journals/j-1");
    });
  });

  it("includes orphans toggle reloads graph", async () => {
    render(
      <MemoryRouter>
        <Graph />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mockGetGraph).toHaveBeenCalledTimes(1);
    });

    const orphanToggle = screen.getByRole("checkbox", { name: /orphan/i });
    fireEvent.click(orphanToggle);

    await waitFor(() => {
      expect(mockGetGraph).toHaveBeenCalledTimes(2);
    });
  });
});
