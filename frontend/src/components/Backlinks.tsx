import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBacklinks } from "../api/mentions";
import type { Backlink } from "../types/mention";

interface BacklinksProps {
  entityType: string;
  entityId: string;
}

export default function Backlinks({ entityType, entityId }: BacklinksProps) {
  const [backlinks, setBacklinks] = useState<Backlink[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getBacklinks(entityType, entityId)
      .then(setBacklinks)
      .catch(() => setBacklinks([]))
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  if (loading) {
    return null;
  }

  return (
    <div className="mt-4">
      <h4 className="mb-2 text-sm font-semibold text-light-text/70">Referenced in Journals</h4>
      {backlinks.length === 0 ? (
        <p className="text-sm text-light-text/40">No journal entries reference this yet.</p>
      ) : (
        <ul className="space-y-2">
          {backlinks.map((bl) => (
            <li key={bl.journal_id} className="rounded bg-dark-bg p-2 text-sm">
              <Link
                to={`/journals/${bl.journal_id}`}
                className="font-medium text-primary hover:underline"
              >
                {bl.title}
              </Link>
              <span className="ml-2 text-light-text/50">{bl.entry_date}</span>
              <p className="mt-1 text-light-text/60">{bl.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
