import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import JournalList from "../src/pages/JournalList";
import JournalEdit from "../src/pages/JournalEdit";

// Mock react-md-editor to avoid complex rendering in tests
vi.mock("@uiw/react-md-editor", () => {
  const commands: Record<string, unknown> = {
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
  const MDEditor = ({
    value,
    onChange,
    "data-testid": testId,
  }: {
    value: string;
    onChange: (v: string) => void;
    "data-testid"?: string;
    commands?: unknown[];
  }) => (
    <textarea
      data-testid={testId || "md-editor"}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
  return { default: MDEditor, commands };
});

const mockListJournals = vi.fn();
const mockDeleteJournal = vi.fn();
const mockCreateJournal = vi.fn();
const mockGetJournal = vi.fn();
const mockUpdateJournal = vi.fn();

vi.mock("../src/api/journals", () => ({
  listJournals: (...args: unknown[]) => mockListJournals(...args),
  deleteJournal: (...args: unknown[]) => mockDeleteJournal(...args),
  createJournal: (...args: unknown[]) => mockCreateJournal(...args),
  getJournal: (...args: unknown[]) => mockGetJournal(...args),
  updateJournal: (...args: unknown[]) => mockUpdateJournal(...args),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: mockId }),
  };
});

let mockId: string | undefined;

beforeEach(() => {
  vi.clearAllMocks();
  mockId = undefined;
});

describe("JournalList", () => {
  it("renders journal list with entries", async () => {
    mockListJournals.mockResolvedValue({
      items: [
        {
          id: "1",
          title: "First Entry",
          content: "Hello",
          entry_date: "2025-01-15",
          created_at: "2025-01-15T00:00:00",
          updated_at: "2025-01-15T00:00:00",
        },
        {
          id: "2",
          title: "Second Entry",
          content: "World",
          entry_date: "2025-01-16",
          created_at: "2025-01-16T00:00:00",
          updated_at: "2025-01-16T00:00:00",
        },
      ],
      total: 2,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <JournalList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("First Entry")).toBeInTheDocument();
    expect(screen.getByText("Second Entry")).toBeInTheDocument();
  });

  it("shows empty state when no entries", async () => {
    mockListJournals.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <JournalList />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("No journal entries yet. Create your first one!"),
    ).toBeInTheDocument();
  });

  it("has a link to create a new entry", async () => {
    mockListJournals.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <JournalList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("New Entry")).toBeInTheDocument();
    expect(screen.getByText("New Entry").closest("a")).toHaveAttribute("href", "/journals/new");
  });

  it("expands and collapses rendered markdown content", async () => {
    const user = userEvent.setup();
    mockListJournals.mockResolvedValue({
      items: [
        {
          id: "1",
          title: "Markdown Entry",
          content: "## Hello\n\nSome **bold** text",
          entry_date: "2025-01-15",
          created_at: "2025-01-15T00:00:00",
          updated_at: "2025-01-15T00:00:00",
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <JournalList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Markdown Entry")).toBeInTheDocument();

    // Content should not be visible initially
    expect(screen.queryByText("Hello")).not.toBeInTheDocument();

    // Click toggle to expand
    const toggle = screen.getByLabelText("Toggle content");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);

    // Rendered markdown content should now be visible
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Hello")).toBeInTheDocument();

    // Click again to collapse
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("Hello")).not.toBeInTheDocument();
  });

  it("can expand multiple journal entries independently", async () => {
    const user = userEvent.setup();
    mockListJournals.mockResolvedValue({
      items: [
        {
          id: "1",
          title: "First",
          content: "Content one",
          entry_date: "2025-01-15",
          created_at: "2025-01-15T00:00:00",
          updated_at: "2025-01-15T00:00:00",
        },
        {
          id: "2",
          title: "Second",
          content: "Content two",
          entry_date: "2025-01-16",
          created_at: "2025-01-16T00:00:00",
          updated_at: "2025-01-16T00:00:00",
        },
      ],
      total: 2,
      page: 1,
      per_page: 20,
    });

    render(
      <MemoryRouter>
        <JournalList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("First")).toBeInTheDocument();

    const toggles = screen.getAllByLabelText("Toggle content");
    expect(toggles).toHaveLength(2);

    // Expand only the first entry
    await user.click(toggles[0]!);
    expect(screen.getByText("Content one")).toBeInTheDocument();
    expect(screen.queryByText("Content two")).not.toBeInTheDocument();

    // Expand the second entry as well
    await user.click(toggles[1]!);
    expect(screen.getByText("Content one")).toBeInTheDocument();
    expect(screen.getByText("Content two")).toBeInTheDocument();
  });
});

describe("JournalEdit", () => {
  it("renders create form for new entry", async () => {
    mockId = "new";

    render(
      <MemoryRouter>
        <JournalEdit />
      </MemoryRouter>,
    );

    expect(screen.getByText("New Journal Entry")).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.getByLabelText("Date")).toBeInTheDocument();
    expect(screen.getByTestId("md-editor")).toBeInTheDocument();
  });

  it("creates a new journal entry on submit", async () => {
    const user = userEvent.setup();
    mockId = "new";
    mockCreateJournal.mockResolvedValue({
      id: "new-id",
      title: "Test",
      content: "Body",
      entry_date: "2025-01-15",
      created_at: "2025-01-15T00:00:00",
      updated_at: "2025-01-15T00:00:00",
    });

    render(
      <MemoryRouter>
        <JournalEdit />
      </MemoryRouter>,
    );

    await user.clear(screen.getByLabelText("Title"));
    await user.type(screen.getByLabelText("Title"), "Test");
    await user.clear(screen.getByTestId("md-editor"));
    await user.type(screen.getByTestId("md-editor"), "Body");

    await user.click(screen.getByText("Create"));

    await waitFor(() => {
      expect(mockCreateJournal).toHaveBeenCalledWith({
        title: "Test",
        content: "Body",
        entry_date: expect.any(String),
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/journals");
    });
  });

  it("loads and edits an existing entry", async () => {
    const user = userEvent.setup();
    mockId = "abc-123";
    mockGetJournal.mockResolvedValue({
      id: "abc-123",
      title: "Existing",
      content: "Old content",
      entry_date: "2025-01-15",
      created_at: "2025-01-15T00:00:00",
      updated_at: "2025-01-15T00:00:00",
    });
    mockUpdateJournal.mockResolvedValue({
      id: "abc-123",
      title: "Updated",
      content: "Old content",
      entry_date: "2025-01-15",
      created_at: "2025-01-15T00:00:00",
      updated_at: "2025-01-15T10:00:00",
    });

    render(
      <MemoryRouter>
        <JournalEdit />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Edit Journal Entry")).toBeInTheDocument();

    const titleInput = screen.getByLabelText("Title");
    await waitFor(() => {
      expect(titleInput).toHaveValue("Existing");
    });

    await user.clear(titleInput);
    await user.type(titleInput, "Updated");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockUpdateJournal).toHaveBeenCalledWith("abc-123", {
        title: "Updated",
        content: "Old content",
        entry_date: "2025-01-15",
      });
    });
  });
});
