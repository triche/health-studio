import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Settings from "../src/pages/Settings";

const mockListApiKeys = vi.fn();
const mockCreateApiKey = vi.fn();
const mockRevokeApiKey = vi.fn();
const mockExportJson = vi.fn();
const mockExportCsv = vi.fn();
const mockExportJournalsMarkdown = vi.fn();
const mockImportJson = vi.fn();
const mockImportCsv = vi.fn();

vi.mock("../src/api/auth", () => ({
  getAuthStatus: vi.fn().mockResolvedValue({ registered: true, authenticated: true }),
  listApiKeys: (...args: unknown[]) => mockListApiKeys(...args),
  createApiKey: (...args: unknown[]) => mockCreateApiKey(...args),
  revokeApiKey: (...args: unknown[]) => mockRevokeApiKey(...args),
}));

vi.mock("../src/api/export", () => ({
  exportJson: (...args: unknown[]) => mockExportJson(...args),
  exportCsv: (...args: unknown[]) => mockExportCsv(...args),
  exportJournalsMarkdown: (...args: unknown[]) => mockExportJournalsMarkdown(...args),
  importJson: (...args: unknown[]) => mockImportJson(...args),
  importCsv: (...args: unknown[]) => mockImportCsv(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockListApiKeys.mockResolvedValue([]);
  // Mock URL.createObjectURL and URL.revokeObjectURL
  global.URL.createObjectURL = vi.fn(() => "blob:http://localhost/fake");
  global.URL.revokeObjectURL = vi.fn();
});

describe("Settings — Export / Import", () => {
  it("renders export section", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/export data/i)).toBeInTheDocument();
  });

  it("renders import section", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/import data/i)).toBeInTheDocument();
  });

  it("exports full JSON backup on button click", async () => {
    const user = userEvent.setup();
    const blob = new Blob(['{"version":1}'], { type: "application/json" });
    mockExportJson.mockResolvedValue(blob);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    const btn = await screen.findByRole("button", { name: /export json/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockExportJson).toHaveBeenCalled();
    });
  });

  it("exports CSV for a selected entity", async () => {
    const user = userEvent.setup();
    const blob = new Blob(["id,name\n1,Weight"], { type: "text/csv" });
    mockExportCsv.mockResolvedValue(blob);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    // Select entity from dropdown
    const select = await screen.findByLabelText(/csv entity/i);
    await user.selectOptions(select, "metric_types");

    const btn = screen.getByRole("button", { name: /export csv/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockExportCsv).toHaveBeenCalledWith("metric_types");
    });
  });

  it("exports journals as markdown", async () => {
    const user = userEvent.setup();
    const blob = new Blob(["# Day One\n"], { type: "text/markdown" });
    mockExportJournalsMarkdown.mockResolvedValue(blob);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    const btn = await screen.findByRole("button", { name: /export markdown/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockExportJournalsMarkdown).toHaveBeenCalled();
    });
  });

  it("imports JSON backup file", async () => {
    const user = userEvent.setup();
    mockImportJson.mockResolvedValue({
      metric_types: 1,
      metric_entries: 2,
      skipped: 0,
    });

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    const fileInput = await screen.findByLabelText(/json backup file/i);
    const file = new File(['{"version":1,"metric_types":[]}'], "backup.json", {
      type: "application/json",
    });
    await user.upload(fileInput, file);

    const btn = await waitFor(() => {
      const b = screen.getByRole("button", { name: /import json/i });
      expect(b).not.toBeDisabled();
      return b;
    });
    await user.click(btn);

    await waitFor(() => {
      expect(mockImportJson).toHaveBeenCalled();
    });
  });

  it("imports CSV file for metrics", async () => {
    const user = userEvent.setup();
    mockImportCsv.mockResolvedValue({ imported: 3 });

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    const select = await screen.findByLabelText(/csv import entity/i);
    await user.selectOptions(select, "metric_entries");

    const fileInput = screen.getByLabelText(/csv file/i);
    const file = new File(["metric_type_id,value,recorded_date\n"], "data.csv", {
      type: "text/csv",
    });
    await user.upload(fileInput, file);

    const btn = screen.getByRole("button", { name: /import csv/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockImportCsv).toHaveBeenCalledWith("metric_entries", expect.any(File));
    });
  });

  it("shows error when import fails", async () => {
    const user = userEvent.setup();
    mockImportJson.mockRejectedValue(new Error("Unsupported export version"));

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    const fileInput = await screen.findByLabelText(/json backup file/i);
    const file = new File(['{"version":999}'], "bad.json", { type: "application/json" });
    await user.upload(fileInput, file);

    const btn = await waitFor(() => {
      const b = screen.getByRole("button", { name: /import json/i });
      expect(b).not.toBeDisabled();
      return b;
    });
    await user.click(btn);

    expect(await screen.findByText(/unsupported export version/i)).toBeInTheDocument();
  });
});
