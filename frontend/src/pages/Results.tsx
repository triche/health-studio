import { useCallback, useEffect, useState } from "react";
import Plot from "react-plotly.js";
import {
  listExerciseTypes,
  createExerciseType,
  deleteExerciseType,
  listResultEntries,
  createResultEntry,
  updateResultEntry,
  deleteResultEntry,
  getResultTrend,
} from "../api/results";
import type { ExerciseType, ResultEntry, ResultTrendResponse } from "../types/result";
import Backlinks from "../components/Backlinks";

export default function Results() {
  const [types, setTypes] = useState<ExerciseType[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState<string | null>(null);
  const [entries, setEntries] = useState<ResultEntry[]>([]);
  const [trend, setTrend] = useState<ResultTrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New type form
  const [newTypeName, setNewTypeName] = useState("");
  const [newTypeCategory, setNewTypeCategory] = useState("custom");
  const [newTypeUnit, setNewTypeUnit] = useState("lbs");
  const [showManage, setShowManage] = useState(false);

  // New entry form
  const [entryValue, setEntryValue] = useState("");
  const [entryHours, setEntryHours] = useState("");
  const [entryMinutes, setEntryMinutes] = useState("");
  const [entrySeconds, setEntrySeconds] = useState("");
  const [entryDate, setEntryDate] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [entryNotes, setEntryNotes] = useState("");
  const [entryIsRx, setEntryIsRx] = useState(false);

  // Inline edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editIsRx, setEditIsRx] = useState(false);

  // Chart visibility
  const [showGraph, setShowGraph] = useState(false);

  const loadTypes = useCallback(async () => {
    try {
      const data = await listExerciseTypes();
      setTypes(data);
      if (data.length > 0 && !selectedTypeId) {
        setSelectedTypeId(data[0]!.id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load exercise types");
    } finally {
      setLoading(false);
    }
  }, [selectedTypeId]);

  const loadEntries = useCallback(async () => {
    if (!selectedTypeId) return;
    try {
      const [entryData, trendData] = await Promise.all([
        listResultEntries({ exercise_type_id: selectedTypeId, per_page: 50 }),
        getResultTrend(selectedTypeId),
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
      const created = await createExerciseType({
        name: newTypeName,
        category: newTypeCategory,
        result_unit: newTypeUnit,
      });
      setTypes((prev) => [...prev, created]);
      setSelectedTypeId(created.id);
      setNewTypeName("");
      setNewTypeCategory("custom");
      setNewTypeUnit("lbs");
      setShowManage(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create exercise type");
    }
  };

  const handleDeleteType = async (id: string) => {
    try {
      await deleteExerciseType(id);
      setTypes((prev) => prev.filter((t) => t.id !== id));
      if (selectedTypeId === id) {
        setSelectedTypeId(types.find((t) => t.id !== id)?.id ?? null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete exercise type");
    }
  };

  const handleLogEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTypeId) return;
    setError(null);
    try {
      const value = isTime
        ? parseInt(entryHours || "0", 10) * 3600 +
          parseInt(entryMinutes || "0", 10) * 60 +
          parseInt(entrySeconds || "0", 10)
        : parseFloat(entryValue);
      await createResultEntry({
        exercise_type_id: selectedTypeId,
        value,
        recorded_date: entryDate,
        is_rx: isCrossFit ? entryIsRx : undefined,
        notes: entryNotes || undefined,
      });
      setEntryValue("");
      setEntryHours("");
      setEntryMinutes("");
      setEntrySeconds("");
      setEntryNotes("");
      setEntryIsRx(false);
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to log result");
    }
  };

  const handleDeleteEntry = async (id: string) => {
    try {
      await deleteResultEntry(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete entry");
    }
  };

  const startEditing = (entry: ResultEntry) => {
    setEditingId(entry.id);
    setEditValue(String(entry.value));
    setEditDate(entry.recorded_date);
    setEditNotes(entry.notes ?? "");
    setEditIsRx(entry.is_rx);
  };

  const cancelEditing = () => {
    setEditingId(null);
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    try {
      await updateResultEntry(editingId, {
        value: parseFloat(editValue),
        recorded_date: editDate,
        is_rx: isCrossFit ? editIsRx : undefined,
        notes: editNotes || undefined,
      });
      setEditingId(null);
      await loadEntries();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update entry");
    }
  };

  const selectedType = types.find((t) => t.id === selectedTypeId);
  const isTime = selectedType?.result_unit === "seconds" || selectedType?.result_unit === "time";
  const isCrossFit = selectedType?.category === "crossfit_benchmark";

  const categoryLabels: Record<string, string> = {
    olympic_lift: "Olympic Lift",
    power_lift: "Power Lift",
    crossfit_benchmark: "CrossFit Benchmark",
    running: "Running",
    custom: "Custom",
  };

  const groupedTypes = types.reduce<Record<string, ExerciseType[]>>((acc, t) => {
    const cat = t.category || "custom";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(t);
    return acc;
  }, {});

  const formatTime = (totalSeconds: number): string => {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = Math.round(totalSeconds % 60);
    const parts: string[] = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0 || parts.length === 0) parts.push(`${s}s`);
    return parts.join(" ");
  };

  if (loading) return <p className="p-6 text-light-text/60">Loading…</p>;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-6 text-3xl font-bold text-light-text">Results</h1>

      {error && <div className="mb-4 rounded-lg bg-red-900/50 p-3 text-red-200">{error}</div>}

      {/* Type selector */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          {types.length > 0 && (
            <>
              <label htmlFor="exercise-type-select" className="text-sm font-medium text-light-text">
                Exercise type
              </label>
              <select
                id="exercise-type-select"
                value={selectedTypeId ?? ""}
                onChange={(e) => setSelectedTypeId(e.target.value)}
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              >
                {Object.entries(groupedTypes).map(([category, categoryTypes]) => (
                  <optgroup key={category} label={categoryLabels[category] ?? category}>
                    {categoryTypes.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.result_unit})
                      </option>
                    ))}
                  </optgroup>
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
                placeholder="Name (e.g. Back Squat)"
                required
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              />
              <select
                value={newTypeCategory}
                onChange={(e) => setNewTypeCategory(e.target.value)}
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              >
                <option value="olympic_lift">Olympic Lift</option>
                <option value="power_lift">Power Lift</option>
                <option value="crossfit_benchmark">CrossFit Benchmark</option>
                <option value="running">Running</option>
                <option value="custom">Custom</option>
              </select>
              <select
                value={newTypeUnit}
                onChange={(e) => setNewTypeUnit(e.target.value)}
                className="rounded-lg border border-gray-600 bg-dark-surface px-3 py-1.5 text-sm text-light-text focus:border-primary focus:outline-none"
              >
                <option value="lbs">lbs</option>
                <option value="reps">reps</option>
                <option value="seconds">seconds</option>
                <option value="time">time</option>
              </select>
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
        <p className="text-light-text/60">No exercise types. Add one to get started!</p>
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
                  <Plot
                    data={[
                      {
                        x: trend.data.map((p) => p.recorded_date),
                        y: trend.data.map((p) => p.value),
                        type: "scatter" as const,
                        mode: "lines+markers" as const,
                        marker: {
                          color: trend.data.map((p) => (p.is_pr ? "#8B5CF6" : "#3B82F6")),
                          size: trend.data.map((p) => (p.is_pr ? 12 : 6)),
                        },
                        line: { color: "#3B82F6" },
                        name: "Value",
                      },
                    ]}
                    layout={{
                      title: {
                        text: `${trend.exercise_name} (${trend.result_unit})`,
                        font: { color: "#F1F5F9" },
                      },
                      paper_bgcolor: "#1E293B",
                      plot_bgcolor: "#1E293B",
                      xaxis: { color: "#94A3B8", gridcolor: "#334155" },
                      yaxis: {
                        color: "#94A3B8",
                        gridcolor: "#334155",
                        title: { text: trend.result_unit },
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
            {isTime ? (
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
                <input
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  value={entrySeconds}
                  onChange={(e) => setEntrySeconds(e.target.value)}
                  placeholder="Seconds"
                  aria-label="Seconds"
                  className="w-24 rounded-lg border border-gray-600 bg-dark-surface px-3 py-2 text-sm text-light-text focus:border-primary focus:outline-none"
                />
              </>
            ) : (
              <input
                type="number"
                step="any"
                value={entryValue}
                onChange={(e) => setEntryValue(e.target.value)}
                placeholder={`Value (${selectedType.result_unit})`}
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
              disabled={isTime ? !entryHours && !entryMinutes && !entrySeconds : !entryValue}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
            >
              Log
            </button>
            {isCrossFit && (
              <label className="flex items-center gap-1.5 text-sm font-medium text-light-text">
                <input
                  type="checkbox"
                  checked={entryIsRx}
                  onChange={(e) => setEntryIsRx(e.target.checked)}
                  aria-label="RX"
                  className="rounded"
                />
                RX
              </label>
            )}
          </form>

          {/* Entry list */}
          {entries.length === 0 ? (
            <p className="text-light-text/60">No entries yet for {selectedType.name}.</p>
          ) : (
            <table className="w-full text-left text-sm text-light-text">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Value ({selectedType.result_unit})</th>
                  <th className="pb-2 font-medium">PR</th>
                  {isCrossFit && <th className="pb-2 font-medium">RX</th>}
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
                          {entry.is_pr && (
                            <span className="rounded bg-purple-600 px-2 py-0.5 text-xs font-bold text-white">
                              PR
                            </span>
                          )}
                        </td>
                        {isCrossFit && (
                          <td className="py-2">
                            <label className="flex items-center gap-1.5 text-sm">
                              <input
                                type="checkbox"
                                checked={editIsRx}
                                onChange={(e) => setEditIsRx(e.target.checked)}
                                aria-label="Edit RX"
                                className="rounded"
                              />
                              RX
                            </label>
                          </td>
                        )}
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
                        <td className="py-2">{isTime ? formatTime(entry.value) : entry.value}</td>
                        <td className="py-2">
                          {entry.is_pr && (
                            <span className="rounded bg-purple-600 px-2 py-0.5 text-xs font-bold text-white">
                              PR
                            </span>
                          )}
                        </td>
                        {isCrossFit && (
                          <td className="py-2">
                            {entry.is_rx && (
                              <span className="rounded bg-teal-600 px-2 py-0.5 text-xs font-bold text-white">
                                RX
                              </span>
                            )}
                          </td>
                        )}
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
      {selectedTypeId && <Backlinks entityType="exercise_type" entityId={selectedTypeId} />}
    </div>
  );
}
