import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import EntityPreview, { clearPreviewCache } from "../src/components/EntityPreview";

const mockGetEntityPreview = vi.fn();

vi.mock("../src/api/preview", () => ({
  getEntityPreview: (...args: unknown[]) => mockGetEntityPreview(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
  clearPreviewCache();
});

describe("EntityPreview", () => {
  it("shows goal preview on hover", async () => {
    mockGetEntityPreview.mockResolvedValue({
      entity_type: "goal",
      entity_id: "g-1",
      title: "Squat 405",
      status: "active",
      progress: 77,
      target_value: 405,
      current_value: 315,
      deadline: "2026-12-31",
    });

    render(
      <MemoryRouter>
        <EntityPreview entityType="goal" entityId="g-1">
          <span>Hover me</span>
        </EntityPreview>
      </MemoryRouter>,
    );

    fireEvent.mouseEnter(screen.getByText("Hover me"));

    await waitFor(() => {
      expect(screen.getByText("Squat 405")).toBeInTheDocument();
    });
    expect(screen.getByText(/77%/)).toBeInTheDocument();
    expect(screen.getByText(/315.*405/)).toBeInTheDocument();
    expect(screen.getByText(/active/i)).toBeInTheDocument();
  });

  it("shows metric preview with trend", async () => {
    mockGetEntityPreview.mockResolvedValue({
      entity_type: "metric_type",
      entity_id: "m-1",
      title: "Body Weight",
      unit: "lbs",
      latest_value: 205,
      latest_date: "2026-04-01",
      trend: [
        { date: "2026-03-25", value: 207 },
        { date: "2026-04-01", value: 205 },
      ],
    });

    render(
      <MemoryRouter>
        <EntityPreview entityType="metric_type" entityId="m-1">
          <span>Hover me</span>
        </EntityPreview>
      </MemoryRouter>,
    );

    fireEvent.mouseEnter(screen.getByText("Hover me"));

    await waitFor(() => {
      expect(screen.getByText("Body Weight")).toBeInTheDocument();
    });
    expect(screen.getByText(/205/)).toBeInTheDocument();
    expect(screen.getByText(/lbs/)).toBeInTheDocument();
  });

  it("shows exercise preview with PR", async () => {
    mockGetEntityPreview.mockResolvedValue({
      entity_type: "exercise_type",
      entity_id: "e-1",
      title: "Back Squat",
      category: "Barbell",
      result_unit: "lbs",
      pr_value: 315,
      pr_date: "2026-03-20",
      recent_results: [
        { date: "2026-03-10", value: 295 },
        { date: "2026-03-20", value: 315 },
      ],
    });

    render(
      <MemoryRouter>
        <EntityPreview entityType="exercise_type" entityId="e-1">
          <span>Hover me</span>
        </EntityPreview>
      </MemoryRouter>,
    );

    fireEvent.mouseEnter(screen.getByText("Hover me"));

    await waitFor(() => {
      expect(screen.getByText("Back Squat")).toBeInTheDocument();
    });
    expect(screen.getByText(/315/)).toBeInTheDocument();
  });

  it("caches preview data (no re-fetch on second hover)", async () => {
    mockGetEntityPreview.mockResolvedValue({
      entity_type: "goal",
      entity_id: "g-1",
      title: "Squat 405",
      status: "active",
      progress: 50,
      target_value: 405,
      current_value: 300,
      deadline: null,
    });

    render(
      <MemoryRouter>
        <EntityPreview entityType="goal" entityId="g-1">
          <span>Hover me</span>
        </EntityPreview>
      </MemoryRouter>,
    );

    // First hover
    fireEvent.mouseEnter(screen.getByText("Hover me"));
    await waitFor(() => {
      expect(screen.getByText("Squat 405")).toBeInTheDocument();
    });

    // Mouse leave
    fireEvent.mouseLeave(screen.getByText("Hover me"));

    // Second hover
    fireEvent.mouseEnter(screen.getByText("Hover me"));
    await waitFor(() => {
      expect(screen.getByText("Squat 405")).toBeInTheDocument();
    });

    // Should only have fetched once
    expect(mockGetEntityPreview).toHaveBeenCalledTimes(1);
  });

  it("shows loading state while fetching", async () => {
    // Return a promise that never resolves to keep loading state
    let resolvePromise: (value: unknown) => void;
    mockGetEntityPreview.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    render(
      <MemoryRouter>
        <EntityPreview entityType="goal" entityId="g-loading">
          <span>Hover me</span>
        </EntityPreview>
      </MemoryRouter>,
    );

    fireEvent.mouseEnter(screen.getByText("Hover me"));

    await waitFor(() => {
      expect(screen.getByTestId("preview-loading")).toBeInTheDocument();
    });

    // Cleanup: resolve the promise to avoid warnings
    resolvePromise!({
      entity_type: "goal",
      entity_id: "g-loading",
      title: "Test",
      status: "active",
      progress: 0,
      target_value: 100,
      current_value: 0,
      deadline: null,
    });
  });
});
