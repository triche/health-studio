import { useEffect, useState } from "react";
import {
  listApiKeys,
  createApiKey,
  revokeApiKey,
  type ApiKeyInfo,
  type ApiKeyCreated,
} from "../api/auth";

export default function Settings() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const loadKeys = async () => {
    try {
      const data = await listApiKeys();
      setKeys(data);
    } catch {
      setError("Failed to load API keys");
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setError("");
    try {
      const key = await createApiKey(newKeyName.trim());
      setCreatedKey(key);
      setNewKeyName("");
      await loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create key");
    }
  };

  const handleRevoke = async (id: string) => {
    setError("");
    try {
      await revokeApiKey(id);
      setCreatedKey(null);
      await loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke key");
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-light-text">Settings</h1>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-light-text">API Keys</h2>
        <p className="mb-4 text-sm text-light-text/70">
          Create API keys for programmatic access to Health Studio. Keys are shown once on creation
          — save them securely.
        </p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
        )}

        {createdKey && (
          <div className="mb-4 rounded-lg border border-accent/30 bg-accent/10 p-4">
            <p className="mb-2 text-sm font-medium text-accent">
              Key created — copy it now. You won&apos;t see it again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 break-all rounded bg-dark-bg px-3 py-2 text-sm text-light-text">
                {createdKey.raw_key}
              </code>
              <button
                onClick={() => handleCopy(createdKey.raw_key)}
                className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-accent/90"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        )}

        <div className="mb-4 flex gap-2">
          <input
            type="text"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name"
            className="flex-1 rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <button
            onClick={handleCreate}
            disabled={!newKeyName.trim()}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
          >
            Create
          </button>
        </div>

        {keys.length === 0 ? (
          <p className="text-sm text-light-text/50">No API keys created yet.</p>
        ) : (
          <div className="space-y-2">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between rounded-lg bg-dark-surface p-3"
              >
                <div>
                  <span className="font-medium text-light-text">{key.name}</span>
                  <span className="ml-2 text-sm text-light-text/50">{key.prefix}…</span>
                  {key.last_used_at && (
                    <span className="ml-2 text-xs text-light-text/40">
                      Last used: {new Date(key.last_used_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleRevoke(key.id)}
                  className="rounded-lg bg-red-500/20 px-3 py-1 text-sm text-red-400 hover:bg-red-500/30"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
