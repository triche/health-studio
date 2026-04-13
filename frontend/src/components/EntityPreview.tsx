import { useCallback, useEffect, useRef, useState } from "react";
import { getEntityPreview } from "../api/preview";
import type {
  EntityPreviewData,
  PreviewGoal,
  PreviewMetricType,
  PreviewExerciseType,
  TrendPoint,
} from "../types/preview";

// Module-level cache so preview data persists across hover cycles
const previewCache = new Map<string, EntityPreviewData>();

// eslint-disable-next-line react-refresh/only-export-components
export function clearPreviewCache(): void {
  previewCache.clear();
}

function cacheKey(type: string, id: string): string {
  return `${type}:${id}`;
}

/** Render a tiny inline SVG sparkline from data points. */
function Sparkline({ points }: { points: TrendPoint[] }) {
  if (points.length < 2) return null;
  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 80;
  const h = 24;
  const coords = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  return (
    <svg width={w} height={h} className="inline-block align-middle">
      <polyline
        points={coords.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-primary"
      />
    </svg>
  );
}

function GoalPreview({ data }: { data: PreviewGoal }) {
  const progressColor =
    data.status === "completed"
      ? "bg-green-500"
      : data.status === "abandoned"
        ? "bg-gray-500"
        : "bg-primary";
  return (
    <div>
      <div className="mb-1 text-sm font-semibold text-light-text">{data.title}</div>
      <div className="mb-1.5 flex items-center gap-2 text-xs text-light-text/70">
        <span className="capitalize">{data.status}</span>
        {data.deadline && <span>· Due {data.deadline}</span>}
      </div>
      <div className="mb-1 h-1.5 overflow-hidden rounded-full bg-dark-bg">
        <div
          className={`h-full rounded-full ${progressColor}`}
          style={{ width: `${Math.min(100, data.progress)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-light-text/60">
        <span>
          {data.current_value} / {data.target_value}
        </span>
        <span>{Math.round(data.progress)}%</span>
      </div>
    </div>
  );
}

function MetricPreview({ data }: { data: PreviewMetricType }) {
  return (
    <div>
      <div className="mb-1 text-sm font-semibold text-light-text">{data.title}</div>
      {data.latest_value != null ? (
        <>
          <div className="mb-1 text-xs text-light-text/70">
            Latest:{" "}
            <span className="font-medium text-light-text">
              {data.latest_value} {data.unit}
            </span>
            {data.latest_date && <span className="ml-1">({data.latest_date})</span>}
          </div>
          <Sparkline points={data.trend} />
        </>
      ) : (
        <div className="text-xs text-light-text/50">No entries yet</div>
      )}
    </div>
  );
}

function ExercisePreview({ data }: { data: PreviewExerciseType }) {
  return (
    <div>
      <div className="mb-1 text-sm font-semibold text-light-text">{data.title}</div>
      <div className="mb-1 text-xs text-light-text/70">
        {data.category} · {data.result_unit}
      </div>
      {data.pr_value != null ? (
        <>
          <div className="mb-1 text-xs text-light-text/70">
            PR:{" "}
            <span className="font-medium text-light-text">
              {data.pr_value} {data.result_unit}
            </span>
            {data.pr_date && <span className="ml-1">({data.pr_date})</span>}
          </div>
          <Sparkline points={data.recent_results} />
        </>
      ) : (
        <div className="text-xs text-light-text/50">No results yet</div>
      )}
    </div>
  );
}

interface EntityPreviewProps {
  entityType: string;
  entityId: string;
  children: React.ReactNode;
}

export default function EntityPreview({ entityType, entityId, children }: EntityPreviewProps) {
  const [data, setData] = useState<EntityPreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLSpanElement>(null);

  const fetchPreview = useCallback(() => {
    const key = cacheKey(entityType, entityId);
    const cached = previewCache.get(key);
    if (cached) {
      setData(cached);
      return;
    }
    setLoading(true);
    getEntityPreview(entityType, entityId)
      .then((result) => {
        previewCache.set(key, result);
        setData(result);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  const handleMouseEnter = useCallback(() => {
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
    setVisible(true);
    if (!data) fetchPreview();
  }, [data, fetchPreview]);

  const handleMouseLeave = useCallback(() => {
    hideTimerRef.current = setTimeout(() => setVisible(false), 200);
  }, []);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, []);

  function renderContent() {
    if (loading && !data) {
      return (
        <div
          data-testid="preview-loading"
          className="flex items-center gap-2 text-xs text-light-text/50"
        >
          <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          Loading…
        </div>
      );
    }
    if (!data) return null;
    switch (data.entity_type) {
      case "goal":
        return <GoalPreview data={data} />;
      case "metric_type":
        return <MetricPreview data={data} />;
      case "exercise_type":
        return <ExercisePreview data={data} />;
      default:
        return null;
    }
  }

  return (
    <span
      ref={containerRef}
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {visible && (
        <div
          className="absolute bottom-full left-0 z-50 mb-2 w-64 rounded-lg border border-gray-600 bg-dark-surface p-3 shadow-lg"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          data-testid="entity-preview-card"
        >
          {renderContent()}
        </div>
      )}
    </span>
  );
}
