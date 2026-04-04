import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../src/App";

vi.mock("../src/api/journals", () => ({
  listJournals: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  deleteJournal: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("App", () => {
  it("renders the journal page by default", async () => {
    render(<App />);
    expect(await screen.findByText("Journal")).toBeInTheDocument();
  });
});
