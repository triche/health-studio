import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Register from "../src/pages/Register";
import Login from "../src/pages/Login";

const mockGetAuthStatus = vi.fn();
const mockBeginRegistration = vi.fn();
const mockCompleteRegistration = vi.fn();
const mockBeginLogin = vi.fn();
const mockCompleteLogin = vi.fn();

vi.mock("../src/api/auth", () => ({
  getAuthStatus: (...args: unknown[]) => mockGetAuthStatus(...args),
  beginRegistration: (...args: unknown[]) => mockBeginRegistration(...args),
  completeRegistration: (...args: unknown[]) => mockCompleteRegistration(...args),
  beginLogin: (...args: unknown[]) => mockBeginLogin(...args),
  completeLogin: (...args: unknown[]) => mockCompleteLogin(...args),
}));

// Mock the WebAuthn browser API
const mockCredentialsCreate = vi.fn();
const mockCredentialsGet = vi.fn();
Object.defineProperty(window, "PublicKeyCredential", {
  value: class {},
  writable: true,
});
Object.defineProperty(navigator, "credentials", {
  value: { create: mockCredentialsCreate, get: mockCredentialsGet },
  writable: true,
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Register", () => {
  it("renders registration form", () => {
    render(
      <MemoryRouter>
        <Register onRegistered={vi.fn()} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/welcome to health studio/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /register/i })).toBeInTheDocument();
  });

  it("calls registration API on submit", async () => {
    const user = userEvent.setup();
    // Backend returns flat JSON with base64url-encoded binary fields (from py_webauthn options_to_json)
    const mockOptions = {
      rp: { name: "Health Studio", id: "localhost" },
      user: { id: "AQ", name: "User", displayName: "User" },
      challenge: "AQID",
      pubKeyCredParams: [{ type: "public-key", alg: -7 }],
      authenticatorSelection: {
        residentKey: "preferred",
        userVerification: "preferred",
      },
      timeout: 60000,
    };
    mockBeginRegistration.mockResolvedValue({ options: JSON.stringify(mockOptions) });

    const mockCredential = {
      id: "test-id",
      rawId: new ArrayBuffer(4),
      response: {
        attestationObject: new ArrayBuffer(4),
        clientDataJSON: new ArrayBuffer(4),
      },
      type: "public-key",
    };
    mockCredentialsCreate.mockResolvedValue(mockCredential);
    mockCompleteRegistration.mockResolvedValue({ id: 1, display_name: "Test" });

    const onRegistered = vi.fn();
    render(
      <MemoryRouter>
        <Register onRegistered={onRegistered} />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText(/display name/i);
    await user.clear(input);
    await user.type(input, "Test User");
    await user.click(screen.getByRole("button", { name: /register/i }));

    await waitFor(() => {
      expect(mockBeginRegistration).toHaveBeenCalledWith("Test User");
      // Verify navigator.credentials.create was called with publicKey wrapper
      // and base64url fields decoded to ArrayBuffers
      expect(mockCredentialsCreate).toHaveBeenCalled();
      const createArg = mockCredentialsCreate.mock.calls[0][0];
      expect(createArg).toHaveProperty("publicKey");
      expect(createArg.publicKey.challenge).toBeInstanceOf(ArrayBuffer);
      expect(createArg.publicKey.user.id).toBeInstanceOf(ArrayBuffer);
    });
  });
});

describe("Login", () => {
  it("renders login page", () => {
    render(
      <MemoryRouter>
        <Login onLoggedIn={vi.fn()} />
      </MemoryRouter>,
    );

    expect(screen.getByText("Health Studio")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in with passkey/i })).toBeInTheDocument();
  });

  it("calls login API on button click", async () => {
    const user = userEvent.setup();
    // Backend returns flat JSON with base64url-encoded binary fields
    const mockOptions = {
      challenge: "AQID",
      rpId: "localhost",
      allowCredentials: [{ id: "dGVzdA", type: "public-key" }],
      timeout: 60000,
    };
    mockBeginLogin.mockResolvedValue({ options: JSON.stringify(mockOptions) });

    const mockAssertion = {
      id: "test-id",
      rawId: new ArrayBuffer(4),
      response: {
        authenticatorData: new ArrayBuffer(4),
        clientDataJSON: new ArrayBuffer(4),
        signature: new ArrayBuffer(4),
      },
      type: "public-key",
    };
    mockCredentialsGet.mockResolvedValue(mockAssertion);
    mockCompleteLogin.mockResolvedValue({ status: "ok" });

    const onLoggedIn = vi.fn();
    render(
      <MemoryRouter>
        <Login onLoggedIn={onLoggedIn} />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /sign in with passkey/i }));

    await waitFor(() => {
      expect(mockBeginLogin).toHaveBeenCalled();
      // Verify navigator.credentials.get was called with publicKey wrapper
      // and base64url fields decoded to ArrayBuffers
      expect(mockCredentialsGet).toHaveBeenCalled();
      const getArg = mockCredentialsGet.mock.calls[0][0];
      expect(getArg).toHaveProperty("publicKey");
      expect(getArg.publicKey.challenge).toBeInstanceOf(ArrayBuffer);
      expect(getArg.publicKey.allowCredentials[0].id).toBeInstanceOf(ArrayBuffer);
    });
  });
});
