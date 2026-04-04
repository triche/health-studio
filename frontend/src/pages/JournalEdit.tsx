import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { getJournal, createJournal, updateJournal } from "../api/journals";
import type { JournalEntry } from "../types/journal";

export default function JournalEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === "new" || !id;

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [entryDate, setEntryDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [preview, setPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isNew && id) {
      setLoading(true);
      getJournal(id)
        .then((entry: JournalEntry) => {
          setTitle(entry.title);
          setContent(entry.content);
          setEntryDate(entry.entry_date);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Failed to load entry");
        })
        .finally(() => setLoading(false));
    }
  }, [id, isNew]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (isNew) {
        await createJournal({ title, content, entry_date: entryDate });
      } else {
        await updateJournal(id!, { title, content, entry_date: entryDate });
      }
      navigate("/journals");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="p-6 text-light-text/60">Loading…</p>;
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-3xl font-bold text-light-text">
        {isNew ? "New Journal Entry" : "Edit Journal Entry"}
      </h1>

      {error && <div className="mb-4 rounded-lg bg-red-900/50 p-3 text-red-200">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="mb-1 block text-sm font-medium text-light-text">
            Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={500}
            className="w-full rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-light-text focus:border-primary focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="entry_date" className="mb-1 block text-sm font-medium text-light-text">
            Date
          </label>
          <input
            id="entry_date"
            type="date"
            value={entryDate}
            onChange={(e) => setEntryDate(e.target.value)}
            required
            className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-light-text focus:border-primary focus:outline-none"
          />
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <label htmlFor="content" className="text-sm font-medium text-light-text">
              Content (Markdown)
            </label>
            <button
              type="button"
              onClick={() => setPreview((p) => !p)}
              className="text-sm text-primary hover:text-blue-400"
            >
              {preview ? "Edit" : "Preview"}
            </button>
          </div>

          {preview ? (
            <div className="prose prose-invert min-h-[200px] max-w-none rounded-lg border border-gray-600 bg-dark-surface p-3">
              <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{content}</ReactMarkdown>
            </div>
          ) : (
            <textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              className="w-full rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 font-mono text-sm text-light-text focus:border-primary focus:outline-none"
            />
          )}
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving || !title.trim()}
            className="rounded-lg bg-primary px-6 py-2 font-medium text-white hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/journals")}
            className="rounded-lg bg-dark-surface px-6 py-2 font-medium text-light-text hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
