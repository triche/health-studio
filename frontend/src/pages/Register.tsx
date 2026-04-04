import { useState } from "react";
import { beginRegistration, completeRegistration } from "../api/auth";

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

interface RegisterProps {
  onRegistered: () => void;
}

export default function Register({ onRegistered }: RegisterProps) {
  const [displayName, setDisplayName] = useState("User");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    setError("");
    setLoading(true);
    try {
      const { options: optionsJson } = await beginRegistration(displayName);
      const raw = JSON.parse(optionsJson);

      // Decode base64url binary fields and wrap for browser WebAuthn API
      raw.challenge = base64urlToBuffer(raw.challenge);
      raw.user.id = base64urlToBuffer(raw.user.id);
      if (raw.excludeCredentials) {
        for (const cred of raw.excludeCredentials) {
          cred.id = base64urlToBuffer(cred.id);
        }
      }

      const credential = (await navigator.credentials.create({
        publicKey: raw,
      })) as PublicKeyCredential;
      if (!credential) {
        setError("Registration was cancelled.");
        return;
      }

      const attestationResponse = credential.response as AuthenticatorAttestationResponse;
      await completeRegistration({
        id: credential.id,
        rawId: bufferToBase64url(credential.rawId),
        response: {
          attestationObject: bufferToBase64url(attestationResponse.attestationObject),
          clientDataJSON: bufferToBase64url(attestationResponse.clientDataJSON),
        },
        type: credential.type,
      });

      onRegistered();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-bg">
      <div className="w-full max-w-md rounded-xl bg-dark-surface p-8">
        <div className="mb-6 flex items-center justify-center gap-2">
          <img src="/logo.png" alt="" className="h-10 w-10" />
          <h1 className="text-2xl font-bold text-light-text">Welcome to Health Studio</h1>
        </div>
        <p className="mb-6 text-center text-sm text-light-text/70">
          Register a passkey to secure your health data. This can only be done once.
        </p>

        <div className="mb-4">
          <label htmlFor="displayName" className="mb-1 block text-sm font-medium text-light-text">
            Display Name
          </label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text focus:border-primary focus:outline-none"
            placeholder="Your name"
          />
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
        )}

        <button
          onClick={handleRegister}
          disabled={loading || !displayName.trim()}
          className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-white hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? "Registering…" : "Register with Passkey"}
        </button>
      </div>
    </div>
  );
}
