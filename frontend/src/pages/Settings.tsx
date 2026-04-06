import { useEffect, useState } from "react";
import {
  listApiKeys,
  createApiKey,
  revokeApiKey,
  type ApiKeyInfo,
  type ApiKeyCreated,
} from "../api/auth";
import {
  exportJson,
  exportCsv,
  exportJournalsMarkdown,
  importJson,
  importCsv,
  type CsvEntity,
  type CsvImportEntity,
} from "../api/export";

export default function Settings() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  // Export / Import state
  const [csvExportEntity, setCsvExportEntity] = useState<CsvEntity>("metric_types");
  const [csvImportEntity, setCsvImportEntity] = useState<CsvImportEntity>("metric_entries");
  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importMessage, setImportMessage] = useState("");

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

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJson = async () => {
    setError("");
    try {
      const blob = await exportJson();
      downloadBlob(blob, "health-studio-export.json");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const handleExportCsv = async () => {
    setError("");
    try {
      const blob = await exportCsv(csvExportEntity);
      downloadBlob(blob, `health-studio-${csvExportEntity}.csv`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const handleExportMarkdown = async () => {
    setError("");
    try {
      const blob = await exportJournalsMarkdown();
      downloadBlob(blob, "health-studio-journals.md");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const handleImportJson = async () => {
    if (!jsonFile) return;
    setError("");
    setImportMessage("");
    try {
      const text = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(new Error("Failed to read file"));
        reader.readAsText(jsonFile);
      });
      const data = JSON.parse(text);
      const result = await importJson(data);
      const parts = Object.entries(result)
        .filter(([k]) => k !== "skipped")
        .map(([k, v]) => `${k}: ${v}`);
      if (result.skipped) parts.push(`skipped: ${result.skipped}`);
      setImportMessage(`Imported — ${parts.join(", ")}`);
      setJsonFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
  };

  const handleImportCsv = async () => {
    if (!csvFile) return;
    setError("");
    setImportMessage("");
    try {
      const result = await importCsv(csvImportEntity, csvFile);
      setImportMessage(`Imported ${result.imported} rows into ${csvImportEntity}`);
      setCsvFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
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

      {/* Export Data */}
      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-light-text">Export Data</h2>
        <p className="mb-4 text-sm text-light-text/70">
          Download your Health Studio data as JSON, CSV, or Markdown.
        </p>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportJson}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              Export JSON
            </button>
            <span className="text-xs text-light-text/50">Full backup (all data)</span>
          </div>

          <div className="flex items-center gap-2">
            <select
              aria-label="CSV entity"
              value={csvExportEntity}
              onChange={(e) => setCsvExportEntity(e.target.value as CsvEntity)}
              className="rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
            >
              <option value="metric_types">Metric Types</option>
              <option value="metric_entries">Metric Entries</option>
              <option value="exercise_types">Exercise Types</option>
              <option value="result_entries">Result Entries</option>
              <option value="journal_entries">Journal Entries</option>
              <option value="goals">Goals</option>
            </select>
            <button
              onClick={handleExportCsv}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              Export CSV
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportMarkdown}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              Export Markdown
            </button>
            <span className="text-xs text-light-text/50">Journals only</span>
          </div>
        </div>
      </section>

      {/* Import Data */}
      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-light-text">Import Data</h2>
        <p className="mb-4 text-sm text-light-text/70">
          Restore from a JSON backup or import CSV data for metrics and results.
        </p>

        {importMessage && (
          <div className="mb-4 rounded-lg bg-green-500/10 p-3 text-sm text-green-400">
            {importMessage}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="json-import" className="mb-1 block text-sm text-light-text/70">
              JSON Backup File
            </label>
            <div className="flex items-center gap-2">
              <input
                id="json-import"
                type="file"
                accept=".json"
                onChange={(e) => setJsonFile(e.target.files?.[0] ?? null)}
                className="flex-1 text-sm text-light-text file:mr-2 file:rounded-lg file:border-0 file:bg-dark-surface file:px-3 file:py-2 file:text-sm file:text-light-text"
              />
              <button
                onClick={handleImportJson}
                disabled={!jsonFile}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-50"
              >
                Import JSON
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="csv-import-entity" className="mb-1 block text-sm text-light-text/70">
              CSV Import Entity
            </label>
            <div className="flex items-center gap-2">
              <select
                id="csv-import-entity"
                aria-label="CSV import entity"
                value={csvImportEntity}
                onChange={(e) => setCsvImportEntity(e.target.value as CsvImportEntity)}
                className="rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
              >
                <option value="metric_entries">Metric Entries</option>
                <option value="result_entries">Result Entries</option>
              </select>
              <label htmlFor="csv-import-file" className="sr-only">
                CSV file
              </label>
              <input
                id="csv-import-file"
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
                className="flex-1 text-sm text-light-text file:mr-2 file:rounded-lg file:border-0 file:bg-dark-surface file:px-3 file:py-2 file:text-sm file:text-light-text"
              />
              <button
                onClick={handleImportCsv}
                disabled={!csvFile}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-50"
              >
                Import CSV
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
