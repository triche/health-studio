import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { search as searchApi } from "../api/search";
import type { SearchResult } from "../types/search";

const TYPE_CONFIG: Record<string, { icon: string; label: string; path: (id: string) => string }> = {
  journal: { icon: "📓", label: "Journals", path: (id) => `/journals/${id}` },
  goal: { icon: "🎯", label: "Goals", path: () => "/goals" },
  metric_type: { icon: "📊", label: "Metrics", path: () => "/metrics" },
  exercise_type: { icon: "🏋️", label: "Exercises", path: () => "/results" },
};

interface SearchPaletteProps {
  open: boolean;
  onClose: () => void;
}

export default function SearchPalette({ open, onClose }: SearchPaletteProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Focus input when palette opens
  useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setSearched(false);
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      const resp = await searchApi(query);
      setResults(resp.results);
      setSearched(true);
      setSelectedIndex(0);
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleSelect = (result: SearchResult) => {
    const config = TYPE_CONFIG[result.entity_type];
    if (config) {
      navigate(config.path(result.entity_id));
    }
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter" && results[selectedIndex]) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Palette */}
      <div className="relative z-10 w-full max-w-lg rounded-xl bg-slate-800 shadow-2xl">
        {/* Search input */}
        <div className="flex items-center border-b border-slate-700 px-4">
          <svg
            className="h-5 w-5 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search across all health data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent px-3 py-3 text-sm text-slate-100 placeholder-slate-400 outline-none"
          />
          <kbd className="hidden rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-400 sm:inline">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {!searched && !query.trim() && (
            <p className="px-3 py-6 text-center text-sm text-slate-400">
              Start typing to search across all your health data
            </p>
          )}

          {searched && results.length === 0 && (
            <p className="px-3 py-6 text-center text-sm text-slate-400">
              No results for &ldquo;{query}&rdquo;
            </p>
          )}

          {results.map((result, index) => {
            const config = TYPE_CONFIG[result.entity_type] ?? {
              icon: "📄",
              label: result.entity_type,
              path: () => "/",
            };
            return (
              <button
                key={`${result.entity_type}-${result.entity_id}`}
                onClick={() => handleSelect(result)}
                className={`flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left text-sm ${
                  index === selectedIndex
                    ? "bg-primary/20 text-slate-100"
                    : "text-slate-300 hover:bg-slate-700"
                }`}
              >
                <span className="mt-0.5 text-base">{config.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{result.title}</div>
                  {result.snippet && (
                    <div
                      className="mt-0.5 truncate text-xs text-slate-400"
                      dangerouslySetInnerHTML={{ __html: result.snippet }}
                    />
                  )}
                  <span className="text-xs text-slate-500">{config.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
