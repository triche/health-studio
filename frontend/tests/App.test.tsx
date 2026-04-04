import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../src/App";

vi.mock("../src/api/journals", () => ({
  listJournals: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  deleteJournal: vi.fn(),
}));

vi.mock("../src/api/metrics", () => ({
  listMetricTypes: vi.fn().mockResolvedValue([]),
  listMetricEntries: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  createMetricType: vi.fn(),
  deleteMetricType: vi.fn(),
  createMetricEntry: vi.fn(),
  deleteMetricEntry: vi.fn(),
  getMetricTrend: vi.fn().mockResolvedValue({ data: [] }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("App", () => {
  it("renders the journal page by default", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Journal" })).toBeInTheDocument();
  });

  it("renders nav links for Journals and Metrics", async () => {
    render(<App />);
    const navLinks = await screen.findAllByRole("link");
    const navTexts = navLinks.map((l) => l.textContent);
    expect(navTexts).toContain("Journal");
    expect(navTexts).toContain("Metrics");
  });
});
