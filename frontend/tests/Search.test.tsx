import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SearchPalette from "../src/components/SearchPalette";

const mockSearch = vi.fn();

vi.mock("../src/api/search", () => ({
  search: (...args: unknown[]) => mockSearch(...args),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SearchPalette", () => {
  it("renders when open", () => {
    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <MemoryRouter>
        <SearchPalette open={false} onClose={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument();
  });

  it("calls onClose on Escape", () => {
    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={onClose} />
      </MemoryRouter>,
    );
    fireEvent.keyDown(screen.getByPlaceholderText(/search/i), { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("shows results grouped by type", async () => {
    mockSearch.mockResolvedValue({
      query: "shoulder",
      results: [
        {
          entity_type: "journal",
          entity_id: "j-1",
          title: "Shoulder Rehab",
          snippet: "...worked on <mark>shoulder</mark> mobility...",
          rank: -4.5,
        },
        {
          entity_type: "goal",
          entity_id: "g-1",
          title: "Shoulder Strength",
          snippet: "",
          rank: -2.1,
        },
        {
          entity_type: "exercise_type",
          entity_id: "e-1",
          title: "Shoulder Press",
          snippet: "",
          rank: -1.0,
        },
      ],
      total: 3,
    });

    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={vi.fn()} />
      </MemoryRouter>,
    );

    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: "shoulder" } });

    await waitFor(() => {
      expect(screen.getByText("Shoulder Rehab")).toBeInTheDocument();
    });
    expect(screen.getByText("Shoulder Strength")).toBeInTheDocument();
    expect(screen.getByText("Shoulder Press")).toBeInTheDocument();
  });

  it("shows no results message", async () => {
    mockSearch.mockResolvedValue({
      query: "nonexistent",
      results: [],
      total: 0,
    });

    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={vi.fn()} />
      </MemoryRouter>,
    );

    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: "nonexistent" } });

    await waitFor(() => {
      expect(screen.getByText(/no results/i)).toBeInTheDocument();
    });
  });

  it("shows placeholder text before searching", () => {
    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText(/start typing/i)).toBeInTheDocument();
  });

  it("navigates to correct page when selecting a journal result", async () => {
    mockSearch.mockResolvedValue({
      query: "test",
      results: [
        {
          entity_type: "journal",
          entity_id: "j-1",
          title: "Test Journal",
          snippet: "",
          rank: -1.0,
        },
      ],
      total: 1,
    });

    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <SearchPalette open={true} onClose={onClose} />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByPlaceholderText(/search/i), { target: { value: "test" } });

    await waitFor(() => {
      expect(screen.getByText("Test Journal")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Test Journal"));
    expect(mockNavigate).toHaveBeenCalledWith("/journals/j-1");
    expect(onClose).toHaveBeenCalled();
  });
});
