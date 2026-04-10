import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getTimeline } from "../api/timeline";
import { listTags } from "../api/tags";
import type { TimelineItem } from "../types/timeline";

const TYPE_CONFIG = {
  journal: {
    icon: "📓",
    label: "Journal",
    color: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
    activeColor: "bg-cyan-500 text-white",
  },
  metric: {
    icon: "📊",
    label: "Metric",
    color: "bg-green-500/10 border-green-500/30 text-green-400",
    activeColor: "bg-green-500 text-white",
  },
  result: {
    icon: "🏋️",
    label: "Result",
    color: "bg-purple-500/10 border-purple-500/30 text-purple-400",
    activeColor: "bg-purple-500 text-white",
  },
  goal: {
    icon: "🎯",
    label: "Goal",
    color: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400",
    activeColor: "bg-yellow-500 text-white",
  },
} as const;

const ALL_TYPES: (keyof typeof TYPE_CONFIG)[] = ["journal", "metric", "result", "goal"];

function getEntityLink(item: TimelineItem): string {
  switch (item.type) {
    case "journal":
      return `/journals/${item.id}`;
    case "goal":
      return "/goals";
    case "metric":
      return "/metrics";
    case "result":
      return "/results";
    default:
      return "/";
  }
}

function TimelineCard({ item, onClick }: { item: TimelineItem; onClick: () => void }) {
  const config = TYPE_CONFIG[item.type] ?? TYPE_CONFIG.journal;

  return (
    <div
      onClick={onClick}
      role="link"
      data-testid={`timeline-card-${item.type}`}
      className={`cursor-pointer rounded-lg border p-4 transition hover:border-slate-600 ${config.color}`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <h3 className="font-semibold text-slate-100">{item.title}</h3>
          {item.type === "result" && Boolean(item.metadata?.is_pr) && (
            <span className="rounded bg-yellow-500 px-1.5 py-0.5 text-xs font-bold text-black">
              PR
            </span>
          )}
        </div>
        <span className="whitespace-nowrap text-xs text-slate-500">{item.date}</span>
      </div>

      <p className="mb-2 text-sm text-slate-400">{item.summary}</p>

      {item.type === "goal" && item.metadata?.progress !== undefined && (
        <div className="mb-2">
          <div className="flex items-center gap-2">
            <div className="h-2 flex-1 rounded-full bg-slate-700">
              <div
                className="h-2 rounded-full bg-yellow-500"
                style={{ width: `${Math.min(100, Number(item.metadata.progress))}%` }}
              />
            </div>
            <span className="text-xs text-slate-400">
              {Math.round(Number(item.metadata.progress))}%
            </span>
          </div>
        </div>
      )}

      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {item.tags.map((tag) => (
            <span
              key={tag}
              className="inline-block rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Timeline() {
  const navigate = useNavigate();
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [activeTypes, setActiveTypes] = useState<Set<string>>(new Set(ALL_TYPES));
  const [tagFilter, setTagFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch available tags for filter
  useEffect(() => {
    listTags()
      .then((tags) => setAvailableTags(tags.map((t: { tag: string }) => t.tag)))
      .catch(() => {});
  }, []);

  const loadTimeline = useCallback(
    async (loadPage: number, append: boolean = false) => {
      setLoading(true);
      setError("");
      try {
        const types = activeTypes.size < ALL_TYPES.length ? [...activeTypes].join(",") : undefined;
        const res = await getTimeline({
          page: loadPage,
          per_page: perPage,
          types,
          tag: tagFilter || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        });
        setItems((prev) => (append ? [...prev, ...res.items] : res.items));
        setTotal(res.total);
        setPage(loadPage);
      } catch {
        setError("Failed to load timeline");
      } finally {
        setLoading(false);
      }
    },
    [activeTypes, tagFilter, dateFrom, dateTo, perPage],
  );

  useEffect(() => {
    loadTimeline(1);
  }, [loadTimeline]);

  const toggleType = (type: string) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const hasMore = items.length < total;

  return (
    <div className="mx-auto max-w-3xl p-4 md:p-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-100">Timeline</h1>

      {/* Filters */}
      <div className="mb-6 space-y-3">
        {/* Type toggles */}
        <div className="flex flex-wrap gap-2">
          {ALL_TYPES.map((type) => {
            const config = TYPE_CONFIG[type]!;
            const isActive = activeTypes.has(type);
            return (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={`rounded-full border px-3 py-1 text-sm font-medium transition ${
                  isActive
                    ? config.activeColor
                    : "border-slate-600 text-slate-500 hover:text-slate-300"
                }`}
              >
                {config.icon} {config.label}
              </button>
            );
          })}
        </div>

        {/* Tag and date filters */}
        <div className="flex flex-wrap gap-2">
          <select
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-300"
          >
            <option value="">All tags</option>
            {availableTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            placeholder="From"
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-300"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            placeholder="To"
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-300"
          />
        </div>
      </div>

      {/* Error */}
      {error && <p className="mb-4 text-red-400">{error}</p>}

      {/* Timeline items */}
      <div className="space-y-3">
        {items.map((item) => (
          <TimelineCard
            key={`${item.type}-${item.id}`}
            item={item}
            onClick={() => navigate(getEntityLink(item))}
          />
        ))}
      </div>

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="py-12 text-center text-slate-500">
          <p className="text-lg">No timeline entries yet</p>
          <p className="mt-1 text-sm">
            Start logging journals, metrics, results, or goals to see your timeline.
          </p>
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="mt-6 text-center">
          <button
            onClick={() => loadTimeline(page + 1, true)}
            disabled={loading}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/80 disabled:opacity-50"
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}

      {/* Loading indicator for initial load */}
      {loading && items.length === 0 && (
        <div className="py-12 text-center text-slate-500">Loading…</div>
      )}
    </div>
  );
}
