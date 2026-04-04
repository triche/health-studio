import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Settings from "../src/pages/Settings";

const mockListApiKeys = vi.fn();
const mockCreateApiKey = vi.fn();
const mockRevokeApiKey = vi.fn();

vi.mock("../src/api/auth", () => ({
  getAuthStatus: vi.fn().mockResolvedValue({ registered: true, authenticated: true }),
  listApiKeys: (...args: unknown[]) => mockListApiKeys(...args),
  createApiKey: (...args: unknown[]) => mockCreateApiKey(...args),
  revokeApiKey: (...args: unknown[]) => mockRevokeApiKey(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Settings", () => {
  it("renders API key management section", async () => {
    mockListApiKeys.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /api keys/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create/i })).toBeInTheDocument();
  });

  it("displays existing API keys", async () => {
    mockListApiKeys.mockResolvedValue([
      {
        id: "key-1",
        name: "CLI Key",
        prefix: "hs_abcde",
        created_at: "2025-01-15T00:00:00",
        last_used_at: null,
      },
    ]);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    expect(await screen.findByText("CLI Key")).toBeInTheDocument();
    expect(screen.getByText(/hs_abcde/)).toBeInTheDocument();
  });

  it("creates a new API key and shows raw key", async () => {
    const user = userEvent.setup();
    mockListApiKeys.mockResolvedValue([]);
    mockCreateApiKey.mockResolvedValue({
      id: "key-new",
      name: "New Key",
      prefix: "hs_newke",
      raw_key: "hs_newkey_full_secret_value",
      created_at: "2025-01-15T00:00:00",
    });

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: /api keys/i });
    const input = screen.getByPlaceholderText(/key name/i);
    await user.type(input, "New Key");
    await user.click(screen.getByRole("button", { name: /create/i }));

    await waitFor(() => {
      expect(mockCreateApiKey).toHaveBeenCalledWith("New Key");
    });

    // Raw key should be displayed
    expect(await screen.findByText(/hs_newkey_full_secret_value/)).toBeInTheDocument();
  });

  it("revokes an API key", async () => {
    const user = userEvent.setup();
    mockListApiKeys.mockResolvedValue([
      {
        id: "key-1",
        name: "Old Key",
        prefix: "hs_oldke",
        created_at: "2025-01-15T00:00:00",
        last_used_at: null,
      },
    ]);
    mockRevokeApiKey.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Old Key")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /revoke/i }));

    await waitFor(() => {
      expect(mockRevokeApiKey).toHaveBeenCalledWith("key-1");
    });
  });
});
