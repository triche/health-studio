import { useCallback, useEffect, useState } from "react";
import Plot from "react-plotly.js";
import {
  listMetricTypes,
  createMetricType,
  deleteMetricType,
  listMetricEntries,
  createMetricEntry,
  updateMetricEntry,
  deleteMetricEntry,
  getMetricTrend,
} from "../api/metrics";
import type { MetricType, MetricEntry, TrendResponse } from "../types/metric";
import Backlinks from "../components/Backlinks";

export default function Metrics() {
  const [types, setTypes] = useState<MetricType[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState<string | null>(null);
  const [entries, setEntries] = useState<MetricEntry[]>([]);
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New type form
  const [newTypeName, setNewTypeName] = useState("");
  const [newTypeUnit, setNewTypeUnit] = useState("");
  const [showManage, setShowManage] = useState(false);

  // New entry form
  const [entryValue, setEntryValue] = useState("");
  const [entryHours, setEntryHours] = useState("");
  const [entryMinutes, setEntryMinutes] = useState("");
  const [entryDate, setEntryDate] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [entryNotes, setEntryNotes] = useState("");

  // Inline edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // Chart options
  const [showGraph, setShowGraph] = useState(false);
  const [showAverage, setShowAverage] = useState(false);

  const loadTypes = useCallback(async () => {
    try {
      const data = await listMetricTypes();
      setTypes(data);
      if (data.length > 0 && !selectedTypeId) {
        setSelectedTypeId(data[0]!.id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load metric types");
    } finally {
      setLoading(false);
    }
  }, [selectedTypeId]);

  const loadEntries = useCallback(async () => {
    if (!selectedTypeId) return;
    try {
      const [entryData, trendData] = await Promise.all([
        listMetricEntries({ metric_type_id: selectedTypeId, per_page: 50 }),
        getMetricTrend(selectedTypeId),
      ]);
      setEntries(entryData.items);
      setTrend(trendData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load entries");
    }
  }, [selectedTypeId]);

  useEffect(() => {
    void loadTypes();
  }, [loadTypes]);

  useEffect(() => {
    void loadEntries();
  }, [loadEntries]);

  const handleCreateType = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const created = await createMetricType({ name: newTypeName, unit: newTypeUnit });
      setTypes((prev) => [...prev, created]);
      setSelectedTypeId(created.id);
      setNewTypeName("");
      setNewTypeUnit("");
      setShowManage(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create metric type");
    }
  };

  const handleDeleteType = async (id: string) => {
    try {
      await deleteMetricType(id);
      setTypes((prev) => prev.filter((t) => t.id !== id));
      if (selectedTypeId === id) {
        setSelectedTypeId(types.find((t) => t.id !== id)?.id ?? null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete metric type");
    }
  };

  const handleLogEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTypeId) return;
    setError(null);
    try {
      const value = isDuration
        ? parseInt(entryHours || "0", 10) * 60 + parseInt(entryMinutes || "0", 10)
        : parseFloat(entryValue);
      await createMetricEntry({
        metric_type_id: selectedTypeId,
        value,
        recorded_date: entryDate,
        notes: entryNotes || undefined,
      });
      setEntryValue("");
      setEntryHours("");
      setEntryMinutes("");
      setEntryNotes("");
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to log entry");
    }
  };

  const handleDeleteEntry = async (id: string) => {
    try {
      await deleteMetricEntry(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete entry");
    }
  };

  const startEditing = (entry: MetricEntry) => {
    setEditingId(entry.id);
    setEditValue(String(entry.value));
    setEditDate(entry.recorded_date);
    setEditNotes(entry.notes ?? "");
  };

  const cancelEditing = () => {
    setEditingId(null);
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    try {
      await updateMetricEntry(editingId, {
        value: parseFloat(editValue),
        recorded_date: editDate,
        notes: editNotes || undefined,
      });
      setEditingId(null);
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update entry");
    }
  };

  const selectedType = types.find((t) => t.id === selectedTypeId);
  const isDuration = selectedType?.unit === "minutes";

  const formatDuration = (totalMinutes: number): string => {
    const h = Math.floor(totalMinutes / 60);
    const m = Math.round(totalMinutes % 60);
    return `${h}h ${m}m`;
  };

  /** Compute a 7-day running average, carrying forward the last value for missing days. */
  const computeRunningAverage = (
    data: { recorded_date: string; value: number }[],
  ): { dates: string[]; values: number[] } => {
    if (data.length === 0) return { dates: [], values: [] };

    // Build a day-by-day map from first to last date, carrying forward
    const sorted = [...data].sort((a, b) => a.recorded_date.localeCompare(b.recorded_date));
    const start = new Date(sorted[0]!.recorded_date + "T00:00:00");
    const end = new Date(sorted[sorted.length - 1]!.recorded_date + "T00:00:00");

    const valueMap = new Map<string, number>();
    for (const pt of sorted) valueMap.set(pt.recorded_date, pt.value);

    const dailyDates: string[] = [];
    const dailyValues: number[] = [];
    let lastValue = sorted[0]!.value;

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const key = d.toISOString().slice(0, 10);
      if (valueMap.has(key)) lastValue = valueMap.get(key)!;
      dailyDates.push(key);
      dailyValues.push(lastValue);
    }

    // Compute rolling 7-day average
    const avgDates: string[] = [];
    const avgValues: number[] = [];
    for (let i = 0; i < dailyValues.length; i++) {
      const windowStart = Math.max(0, i - 6);
      const window = dailyValues.slice(windowStart, i + 1);
      const avg = window.reduce((s, v) => s + v, 0) / window.length;
      avgDates.push(dailyDates[i]!);
      avgValues.push(Math.round(avg * 100) / 100);
    }

    return { dates: avgDates, values: avgValues };
  };

  if (loading) return <p className="p-6 text-light-text/60">Loading…</p>;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-3xl font-bold text-light-text">Metrics</h1>

      {error && <div className="mb-4 rounded-lg bg-red-900/50 p-3 text-red-200">{error}</div>}

      {/* Type selector */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          {types.length > 0 && (
            <>
              <label htmlFor="metric-type-select" className="text-sm font-medium text-light-text">
                Metric type
              </label>
              <select
                id="metric-type-select"
                value={selectedTypeId ?? ""}
                onChange={(e) => setSelectedTypeId(e.target.value)}
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              >
                {types.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.unit})
                  </option>
                ))}
              </select>
            </>
          )}
          <button
            onClick={() => setShowManage((p) => !p)}
            aria-label="Manage types"
            className="rounded-lg bg-dark-surface px-3 py-1.5 text-sm text-accent hover:bg-gray-600"
          >
            Manage
          </button>
        </div>

        {showManage && (
          <div className="mt-2 rounded-lg bg-dark-surface p-4">
            {types.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {types.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center gap-1 rounded-lg bg-gray-700 px-2 py-1"
                  >
                    <span className="text-sm text-light-text">{t.name}</span>
                    <button
                      onClick={() => handleDeleteType(t.id)}
                      className="text-sm text-red-400 hover:text-red-300"
                      aria-label={`Delete ${t.name}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            <form onSubmit={handleCreateType} className="flex gap-2">
              <input
                type="text"
                value={newTypeName}
                onChange={(e) => setNewTypeName(e.target.value)}
                placeholder="Name (e.g. Weight)"
                required
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              />
              <input
                type="text"
                value={newTypeUnit}
                onChange={(e) => setNewTypeUnit(e.target.value)}
                placeholder="Unit (e.g. lbs)"
                required
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              />
              <button
                type="submit"
                className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-600"
              >
                Create
              </button>
            </form>
          </div>
        )}
      </div>

      {!selectedType ? (
        <p className="text-light-text/60">No metric types. Add one to get started!</p>
      ) : (
        <>
          {/* Trend chart */}
          {trend && trend.data.length > 0 && (
            <>
              <button
                type="button"
                onClick={() => setShowGraph((v) => !v)}
                aria-label="Show graph"
                className="mb-3 rounded-lg bg-dark-surface px-3 py-1.5 text-sm text-light-text hover:bg-gray-600"
                title={showGraph ? "Hide graph" : "Show graph"}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="inline-block h-4 w-4"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <polyline points="20 12 17 12 15 18 9 6 7 12 4 12" />
                </svg>
              </button>
              {showGraph && (
                <div className="mb-6 rounded-lg bg-dark-surface p-4">
                  <label className="mb-2 flex items-center gap-2 text-sm text-light-text">
                    <input
                      type="checkbox"
                      checked={showAverage}
                      onChange={(e) => setShowAverage(e.target.checked)}
                      className="rounded"
                    />
                    7-day average
                  </label>
                  <Plot
                    data={[
                      {
                        x: trend.data.map((p) => p.recorded_date),
                        y: trend.data.map((p) => p.value),
                        type: "scatter" as const,
                        mode: "lines+markers" as const,
                        marker: { color: "#3B82F6" },
                        line: { color: "#3B82F6" },
                        name: "Value",
                      },
                      ...(showAverage
                        ? [
                            {
                              x: computeRunningAverage(trend.data).dates,
                              y: computeRunningAverage(trend.data).values,
                              type: "scatter" as const,
                              mode: "lines" as const,
                              line: { color: "#14B8A6", dash: "dash" as const, width: 2 },
                              name: "7-day avg",
                            },
                          ]
                        : []),
                    ]}
                    layout={{
                      title: {
                        text: `${trend.metric_name} (${trend.unit})`,
                        font: { color: "#F1F5F9" },
                      },
                      paper_bgcolor: "#1E293B",
                      plot_bgcolor: "#1E293B",
                      xaxis: { color: "#94A3B8", gridcolor: "#334155" },
                      yaxis: {
                        color: "#94A3B8",
                        gridcolor: "#334155",
                        title: { text: trend.unit },
                      },
                      margin: { t: 40, r: 20, b: 40, l: 60 },
                      legend: { font: { color: "#F1F5F9" } },
                      autosize: true,
                    }}
                    useResizeHandler
                    style={{ width: "100%", height: 300 }}
                    config={{ displayModeBar: false }}
                  />
                </div>
              )}
            </>
          )}

          {/* Log entry form */}
          <form onSubmit={handleLogEntry} className="mb-6 flex flex-wrap gap-2">
            {isDuration ? (
              <>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={entryHours}
                  onChange={(e) => setEntryHours(e.target.value)}
                  placeholder="Hours"
                  aria-label="Hours"
                  className="w-20 rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
                />
                <input
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  value={entryMinutes}
                  onChange={(e) => setEntryMinutes(e.target.value)}
                  placeholder="Minutes"
                  aria-label="Minutes"
                  className="w-24 rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
                />
              </>
            ) : (
              <input
                type="number"
                step="any"
                value={entryValue}
                onChange={(e) => setEntryValue(e.target.value)}
                placeholder={`Value (${selectedType.unit})`}
                required
                aria-label="Value"
                className="w-32 rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
              />
            )}
            <input
              type="date"
              value={entryDate}
              onChange={(e) => setEntryDate(e.target.value)}
              required
              aria-label="Date"
              className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
            />
            <input
              type="text"
              value={entryNotes}
              onChange={(e) => setEntryNotes(e.target.value)}
              placeholder="Notes (optional)"
              aria-label="Notes"
              className="flex-1 rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
            />
            <button
              type="submit"
              disabled={isDuration ? !entryHours && !entryMinutes : !entryValue}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
            >
              Log
            </button>
          </form>

          {/* Entry list */}
          {entries.length === 0 ? (
            <p className="text-light-text/60">No entries yet for {selectedType.name}.</p>
          ) : (
            <table className="w-full text-left text-sm text-light-text">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">
                    Value{isDuration ? "" : ` (${selectedType.unit})`}
                  </th>
                  <th className="pb-2 font-medium">Notes</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-700/50">
                    {editingId === entry.id ? (
                      <>
                        <td className="py-2">
                          <input
                            type="date"
                            value={editDate}
                            onChange={(e) => setEditDate(e.target.value)}
                            aria-label="Edit date"
                            className="rounded border border-gray-600 bg-dark-surface px-2 py-1 text-sm text-light-text"
                          />
                        </td>
                        <td className="py-2">
                          <input
                            type="number"
                            step="any"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            aria-label="Edit value"
                            className="w-24 rounded border border-gray-600 bg-dark-surface px-2 py-1 text-sm text-light-text"
                          />
                        </td>
                        <td className="py-2">
                          <input
                            type="text"
                            value={editNotes}
                            onChange={(e) => setEditNotes(e.target.value)}
                            aria-label="Edit notes"
                            className="w-full rounded border border-gray-600 bg-dark-surface px-2 py-1 text-sm text-light-text"
                          />
                        </td>
                        <td className="py-2 text-right">
                          <button
                            onClick={handleSaveEdit}
                            className="mr-2 text-green-400 hover:text-green-300"
                          >
                            Save
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="text-light-text/60 hover:text-light-text"
                          >
                            Cancel
                          </button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-2">{entry.recorded_date}</td>
                        <td className="py-2">
                          {isDuration ? formatDuration(entry.value) : entry.value}
                        </td>
                        <td className="py-2 text-light-text/60">{entry.notes ?? ""}</td>
                        <td className="py-2 text-right">
                          <button
                            onClick={() => startEditing(entry)}
                            className="mr-2 text-blue-400 hover:text-blue-300"
                            aria-label="Edit entry"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteEntry(entry.id)}
                            className="text-red-400 hover:text-red-300"
                            aria-label="Delete entry"
                          >
                            Delete
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* Backlinks */}
      {selectedTypeId && <Backlinks entityType="metric_type" entityId={selectedTypeId} />}
    </div>
  );
}
