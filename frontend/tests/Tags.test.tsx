import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagInput from "../src/components/TagInput";
import TagList from "../src/components/TagList";

const mockListTags = vi.fn();
const mockGetEntitiesByTag = vi.fn();

vi.mock("../src/api/tags", () => ({
  listTags: (...args: unknown[]) => mockListTags(...args),
  getEntitiesByTag: (...args: unknown[]) => mockGetEntitiesByTag(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockListTags.mockResolvedValue([]);
});

describe("TagInput", () => {
  it("renders existing tags as pills", () => {
    render(<TagInput tags={["strength", "recovery"]} onChange={() => {}} />);
    expect(screen.getByText("strength")).toBeInTheDocument();
    expect(screen.getByText("recovery")).toBeInTheDocument();
  });

  it("adds tag on Enter", async () => {
    const onChange = vi.fn();
    render(<TagInput tags={[]} onChange={onChange} />);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, "strength{Enter}");
    expect(onChange).toHaveBeenCalledWith(["strength"]);
  });

  it("adds tag on comma", async () => {
    const onChange = vi.fn();
    render(<TagInput tags={[]} onChange={onChange} />);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, "recovery,");
    expect(onChange).toHaveBeenCalledWith(["recovery"]);
  });

  it("removes tag on click", async () => {
    const onChange = vi.fn();
    render(<TagInput tags={["strength", "recovery"]} onChange={onChange} />);
    const removeButtons = screen.getAllByRole("button", { name: /remove/i });
    await userEvent.click(removeButtons[0]);
    expect(onChange).toHaveBeenCalledWith(["recovery"]);
  });

  it("normalizes tags to lowercase", async () => {
    const onChange = vi.fn();
    render(<TagInput tags={[]} onChange={onChange} />);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, "STRENGTH{Enter}");
    expect(onChange).toHaveBeenCalledWith(["strength"]);
  });

  it("does not add duplicate tags", async () => {
    const onChange = vi.fn();
    render(<TagInput tags={["strength"]} onChange={onChange} />);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.type(input, "strength{Enter}");
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows autocomplete suggestions", async () => {
    mockListTags.mockResolvedValue([
      { tag: "strength", count: 5 },
      { tag: "recovery", count: 3 },
    ]);
    render(<TagInput tags={[]} onChange={() => {}} />);
    const input = screen.getByPlaceholderText(/add tag/i);
    await userEvent.click(input);
    await userEvent.type(input, "str");
    await waitFor(() => {
      expect(screen.getByText("strength")).toBeInTheDocument();
    });
  });
});

describe("TagList", () => {
  it("renders clickable tag pills", () => {
    render(
      <MemoryRouter>
        <TagList tags={["strength", "recovery"]} />
      </MemoryRouter>,
    );
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveTextContent("strength");
    expect(links[1]).toHaveTextContent("recovery");
  });

  it("links tags to filtered views", () => {
    render(
      <MemoryRouter>
        <TagList tags={["strength"]} baseUrl="/journals" />
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "strength" });
    expect(link).toHaveAttribute("href", "/journals?tag=strength");
  });

  it("renders empty when no tags", () => {
    const { container } = render(
      <MemoryRouter>
        <TagList tags={[]} />
      </MemoryRouter>,
    );
    expect(container.textContent).toBe("");
  });
});
