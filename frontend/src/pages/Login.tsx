import { useState } from "react";
import { beginLogin, completeLogin } from "../api/auth";

function bufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64urlToBuffer(base64url: string): ArrayBuffer {
  const base64 = base64url.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

interface LoginProps {
  onLoggedIn: () => void;
}

export default function Login({ onLoggedIn }: LoginProps) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const { options: optionsJson } = await beginLogin();
      const raw = JSON.parse(optionsJson);

      // Decode base64url binary fields and wrap for browser WebAuthn API
      raw.challenge = base64urlToBuffer(raw.challenge);
      if (raw.allowCredentials) {
        for (const cred of raw.allowCredentials) {
          cred.id = base64urlToBuffer(cred.id);
        }
      }

      const assertion = (await navigator.credentials.get({
        publicKey: raw,
      })) as PublicKeyCredential;
      if (!assertion) {
        setError("Authentication was cancelled.");
        return;
      }

      const authResponse = assertion.response as AuthenticatorAssertionResponse;
      await completeLogin({
        id: assertion.id,
        rawId: bufferToBase64url(assertion.rawId),
        response: {
          authenticatorData: bufferToBase64url(authResponse.authenticatorData),
          clientDataJSON: bufferToBase64url(authResponse.clientDataJSON),
          signature: bufferToBase64url(authResponse.signature),
        },
        type: assertion.type,
      });

      onLoggedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-bg">
      <div className="w-full max-w-md rounded-xl bg-dark-surface p-8">
        <div className="mb-6 flex items-center justify-center gap-2">
          <img src="/logo.png" alt="" className="h-10 w-10" />
          <h1 className="text-2xl font-bold text-light-text">Health Studio</h1>
        </div>
        <p className="mb-6 text-center text-sm text-light-text/70">
          Sign in with your passkey to access your health data.
        </p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-white hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in with Passkey"}
        </button>
      </div>
    </div>
  );
}
