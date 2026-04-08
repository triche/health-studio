import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listTags, getEntitiesByTag } from "../api/tags";
import type { TagCount, TagEntity } from "../types/tag";

const ENTITY_TYPE_LABELS: Record<string, string> = {
  journal: "Journal",
  goal: "Goal",
  metric_type: "Metric",
  exercise_type: "Exercise",
};

const ENTITY_TYPE_ROUTES: Record<string, string> = {
  journal: "/journals",
  goal: "/goals",
  metric_type: "/metrics",
  exercise_type: "/results",
};

export default function Tags() {
  const [tags, setTags] = useState<TagCount[]>([]);
  const [entities, setEntities] = useState<TagEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedTag = searchParams.get("tag") ?? "";
  const typeFilter = searchParams.get("type") ?? "";

  useEffect(() => {
    setLoading(true);
    listTags()
      .then(setTags)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load tags"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedTag) {
      setEntities([]);
      return;
    }
    getEntitiesByTag(selectedTag, typeFilter || undefined)
      .then((res) => setEntities(res.entities))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load tag"));
  }, [selectedTag, typeFilter]);

  const getEntityLink = (entity: TagEntity) => {
    const base = ENTITY_TYPE_ROUTES[entity.entity_type] ?? "/";
    if (entity.entity_type === "journal") return `${base}/${entity.entity_id}`;
    return base;
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-3xl font-bold text-light-text">Tags</h1>

      {error && <div className="mb-4 rounded-lg bg-red-900/50 p-3 text-red-200">{error}</div>}

      {loading ? (
        <p className="text-light-text/60">Loading…</p>
      ) : !selectedTag ? (
        tags.length === 0 ? (
          <p className="text-light-text/60">
            No tags yet. Add tags to your entities to see them here.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {tags.map((t) => (
              <button
                key={t.tag}
                onClick={() => setSearchParams({ tag: t.tag })}
                className="inline-flex items-center gap-1.5 rounded-full bg-primary/20 px-3 py-1 text-sm font-medium text-primary hover:bg-primary/30"
              >
                {t.tag}
                <span className="text-xs text-primary/60">{t.count}</span>
              </button>
            ))}
          </div>
        )
      ) : (
        <>
          <div className="mb-4 flex items-center gap-2">
            <button
              onClick={() => setSearchParams({})}
              className="text-sm text-primary hover:underline"
            >
              ← All Tags
            </button>
            <span className="rounded-full bg-primary/20 px-3 py-0.5 text-sm font-medium text-primary">
              {selectedTag}
            </span>
            {typeFilter && (
              <button
                onClick={() => setSearchParams({ tag: selectedTag })}
                className="text-xs text-light-text/50 hover:text-light-text"
              >
                Clear filter
              </button>
            )}
          </div>

          <div className="mb-4 flex gap-2">
            {["journal", "goal", "metric_type", "exercise_type"].map((type) => (
              <button
                key={type}
                onClick={() =>
                  setSearchParams(
                    typeFilter === type ? { tag: selectedTag } : { tag: selectedTag, type },
                  )
                }
                className={`rounded-lg px-3 py-1 text-xs font-medium ${
                  typeFilter === type
                    ? "bg-primary text-white"
                    : "bg-dark-surface text-light-text/70 hover:text-light-text"
                }`}
              >
                {ENTITY_TYPE_LABELS[type]}
              </button>
            ))}
          </div>

          {entities.length === 0 ? (
            <p className="text-light-text/60">No entities found with this tag.</p>
          ) : (
            <ul className="space-y-2">
              {entities.map((entity) => (
                <li
                  key={`${entity.entity_type}-${entity.entity_id}`}
                  className="rounded-lg bg-dark-surface p-3"
                >
                  <Link to={getEntityLink(entity)} className="text-light-text hover:text-primary">
                    <span className="mr-2 rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary/70">
                      {ENTITY_TYPE_LABELS[entity.entity_type] ?? entity.entity_type}
                    </span>
                    {entity.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
