import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listJournals, deleteJournal } from "../api/journals";
import type { JournalEntry } from "../types/journal";

export default function JournalList() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const page = Number(searchParams.get("page") ?? "1");
  const perPage = 20;

  useEffect(() => {
    setLoading(true);
    setError(null);
    listJournals({ page, per_page: perPage })
      .then((data) => {
        setEntries(data.items);
        setTotal(data.total);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load journals");
      })
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / perPage);

  const handleDelete = async (id: string) => {
    try {
      await deleteJournal(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-light-text">Journal</h1>
        <Link
          to="/journals/new"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
        >
          New Entry
        </Link>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-900/50 p-3 text-red-200">{error}</div>}

      {loading ? (
        <p className="text-light-text/60">Loading…</p>
      ) : entries.length === 0 ? (
        <p className="text-light-text/60">No journal entries yet. Create your first one!</p>
      ) : (
        <>
          <ul className="space-y-3">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="flex items-center justify-between rounded-lg bg-dark-surface p-4"
              >
                <Link
                  to={`/journals/${entry.id}`}
                  className="min-w-0 flex-1 text-light-text hover:text-primary"
                >
                  <h2 className="truncate text-lg font-semibold">{entry.title}</h2>
                  <p className="text-sm text-light-text/60">{entry.entry_date}</p>
                </Link>
                <button
                  onClick={() => handleDelete(entry.id)}
                  className="ml-4 text-sm text-red-400 hover:text-red-300"
                  aria-label={`Delete ${entry.title}`}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>

          {totalPages > 1 && (
            <div className="mt-6 flex justify-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setSearchParams({ page: String(page - 1) })}
                className="rounded bg-dark-surface px-3 py-1 text-light-text disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-light-text/60">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setSearchParams({ page: String(page + 1) })}
                className="rounded bg-dark-surface px-3 py-1 text-light-text disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
