import { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listGoals, createGoal, updateGoal, deleteGoal } from "../api/goals";
import { listMetricTypes } from "../api/metrics";
import { listExerciseTypes } from "../api/results";
import type { Goal, GoalCreate } from "../types/goal";
import type { MetricType } from "../types/metric";
import type { ExerciseType } from "../types/result";

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [metricTypes, setMetricTypes] = useState<MetricType[]>([]);
  const [exerciseTypes, setExerciseTypes] = useState<ExerciseType[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [expandedPlans, setExpandedPlans] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [plan, setPlan] = useState("");
  const [targetType, setTargetType] = useState("metric");
  const [targetId, setTargetId] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [startValue, setStartValue] = useState("");
  const [lowerIsBetter, setLowerIsBetter] = useState(false);
  const [deadline, setDeadline] = useState("");

  const loadGoals = useCallback(async () => {
    try {
      const params: { status?: string } = {};
      if (statusFilter) params.status = statusFilter;
      const res = await listGoals(params);
      setGoals(res.items);
    } catch {
      setError("Failed to load goals");
    }
  }, [statusFilter]);

  const loadTypes = useCallback(async () => {
    try {
      const [mt, et] = await Promise.all([listMetricTypes(), listExerciseTypes()]);
      setMetricTypes(mt);
      setExerciseTypes(et);
    } catch {
      // types are optional for display
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  useEffect(() => {
    loadTypes();
  }, [loadTypes]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setPlan("");
    setTargetType("metric");
    setTargetId("");
    setTargetValue("");
    setStartValue("");
    setLowerIsBetter(false);
    setDeadline("");
    setEditingGoal(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingGoal) {
        await updateGoal(editingGoal.id, {
          title,
          description,
          plan,
          target_type: targetType,
          target_id: targetId,
          target_value: parseFloat(targetValue),
          start_value: startValue ? parseFloat(startValue) : null,
          lower_is_better: lowerIsBetter,
          deadline: deadline || undefined,
        });
      } else {
        const data: GoalCreate = {
          title,
          description,
          plan,
          target_type: targetType,
          target_id: targetId,
          target_value: parseFloat(targetValue),
          lower_is_better: lowerIsBetter,
        };
        if (startValue) data.start_value = parseFloat(startValue);
        if (deadline) data.deadline = deadline;
        await createGoal(data);
      }
      resetForm();
      loadGoals();
    } catch {
      setError("Failed to save goal");
    }
  };

  const handleEdit = (goal: Goal) => {
    setEditingGoal(goal);
    setTitle(goal.title);
    setDescription(goal.description);
    setPlan(goal.plan);
    setTargetType(goal.target_type);
    setTargetId(goal.target_id);
    setTargetValue(String(goal.target_value));
    setStartValue(goal.start_value != null ? String(goal.start_value) : "");
    setLowerIsBetter(goal.lower_is_better);
    setDeadline(goal.deadline || "");
    setShowForm(true);
  };

  const handleComplete = async (goal: Goal) => {
    try {
      await updateGoal(goal.id, { status: "completed" });
      loadGoals();
    } catch {
      setError("Failed to update goal");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteGoal(id);
      loadGoals();
    } catch {
      setError("Failed to delete goal");
    }
  };

  const getTargetName = (goal: Goal) => {
    if (goal.target_type === "metric") {
      const mt = metricTypes.find((m) => m.id === goal.target_id);
      return mt ? `${mt.name} (${mt.unit})` : goal.target_id;
    }
    const et = exerciseTypes.find((e) => e.id === goal.target_id);
    return et ? `${et.name} (${et.result_unit})` : goal.target_id;
  };

  const targetOptions =
    targetType === "metric"
      ? metricTypes.map((mt) => ({ value: mt.id, label: `${mt.name} (${mt.unit})` }))
      : exerciseTypes.map((et) => ({
          value: et.id,
          label: `${et.name} (${et.result_unit})`,
        }));

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-light-text">Goals</h1>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/80"
        >
          New Goal
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</div>
      )}

      {/* Status filter */}
      <div className="mb-4">
        <label htmlFor="status-filter" className="mr-2 text-sm text-light-text/70">
          Filter:
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-light-text/20 bg-dark-surface px-3 py-1.5 text-sm text-light-text"
        >
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="abandoned">Abandoned</option>
        </select>
      </div>

      {/* Create / Edit form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 rounded-lg bg-dark-surface p-4">
          <h2 className="mb-4 text-lg font-semibold text-light-text">
            {editingGoal ? "Edit Goal" : "Create Goal"}
          </h2>
          <div className="mb-3">
            <label htmlFor="goal-title" className="mb-1 block text-sm text-light-text/70">
              Title
            </label>
            <input
              id="goal-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="goal-description" className="mb-1 block text-sm text-light-text/70">
              Description
            </label>
            <textarea
              id="goal-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
              rows={2}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="goal-plan" className="mb-1 block text-sm text-light-text/70">
              Plan (Markdown)
            </label>
            <textarea
              id="goal-plan"
              data-testid="md-editor"
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
              rows={4}
            />
          </div>
          <div className="mb-3 grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="target-type" className="mb-1 block text-sm text-light-text/70">
                Target Type
              </label>
              <select
                id="target-type"
                value={targetType}
                onChange={(e) => {
                  setTargetType(e.target.value);
                  setTargetId("");
                }}
                className="w-full rounded-lg border border-light-text/20 bg-dark-surface px-3 py-2 text-light-text"
              >
                <option value="metric">Metric</option>
                <option value="result">Exercise Result</option>
              </select>
            </div>
            <div>
              <label htmlFor="target-id" className="mb-1 block text-sm text-light-text/70">
                Target
              </label>
              <select
                id="target-id"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className="w-full rounded-lg border border-light-text/20 bg-dark-surface px-3 py-2 text-light-text"
                required
              >
                <option value="">Select...</option>
                {targetOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="mb-3 grid grid-cols-3 gap-3">
            <div>
              <label htmlFor="target-value" className="mb-1 block text-sm text-light-text/70">
                Target Value
              </label>
              <input
                id="target-value"
                type="number"
                step="any"
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
                required
              />
            </div>
            <div>
              <label htmlFor="start-value" className="mb-1 block text-sm text-light-text/70">
                Starting Value
              </label>
              <input
                id="start-value"
                type="number"
                step="any"
                value={startValue}
                onChange={(e) => setStartValue(e.target.value)}
                className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
                placeholder="Optional"
              />
            </div>
            <div>
              <label htmlFor="deadline" className="mb-1 block text-sm text-light-text/70">
                Deadline
              </label>
              <input
                id="deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full rounded-lg border border-light-text/20 bg-dark-bg px-3 py-2 text-light-text"
              />
            </div>
          </div>
          <div className="mb-3">
            <label className="flex items-center gap-2 text-sm text-light-text/70">
              <input
                type="checkbox"
                checked={lowerIsBetter}
                onChange={(e) => setLowerIsBetter(e.target.checked)}
                className="rounded border-light-text/20"
              />
              Lower is better
            </label>
            <p className="mt-1 text-xs text-light-text/50">
              Check this for goals where the number should go down (e.g. body weight, time)
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/80"
            >
              Save Goal
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg bg-dark-bg px-4 py-2 text-sm font-medium text-light-text/70 hover:text-light-text"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Goals list */}
      {goals.length === 0 ? (
        <p className="text-center text-light-text/50">No goals yet. Create one to get started!</p>
      ) : (
        <div className="space-y-4">
          {goals.map((goal) => (
            <div key={goal.id} className="rounded-lg bg-dark-surface p-4">
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-light-text">{goal.title}</h3>
                  {goal.description && (
                    <p className="mt-1 text-sm text-light-text/70">{goal.description}</p>
                  )}
                  <p className="mt-1 text-xs text-light-text/50">
                    Target: {getTargetName(goal)} → {goal.target_value}
                    {goal.start_value != null && ` · Start: ${goal.start_value}`}
                    {goal.deadline && ` · Due: ${goal.deadline}`}
                  </p>
                  <p className="mt-1 text-xs text-light-text/50">
                    {goal.lower_is_better ? "↓ Lower is better" : "↑ Higher is better"}
                  </p>
                </div>
                <div className="flex gap-2">
                  {goal.status === "active" && (
                    <button
                      onClick={() => handleComplete(goal)}
                      className="rounded-lg bg-accent/20 px-3 py-1 text-xs font-medium text-accent hover:bg-accent/30"
                    >
                      Complete
                    </button>
                  )}
                  <button
                    onClick={() => handleEdit(goal)}
                    className="rounded-lg bg-dark-bg px-3 py-1 text-xs font-medium text-light-text/70 hover:text-light-text"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(goal.id)}
                    className="rounded-lg bg-red-500/20 px-3 py-1 text-xs font-medium text-red-400 hover:bg-red-500/30"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-3">
                <div className="mb-1 flex justify-between text-xs text-light-text/70">
                  <span>
                    {goal.current_value} / {goal.target_value}
                  </span>
                  <span>{Math.round(goal.progress)}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-dark-bg">
                  <div
                    className={`h-full rounded-full transition-all ${
                      goal.status === "completed" ? "bg-accent" : "bg-primary"
                    }`}
                    style={{ width: `${Math.min(100, goal.progress)}%` }}
                  />
                </div>
              </div>

              {/* Status badge */}
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                    goal.status === "active"
                      ? "bg-primary/20 text-primary"
                      : goal.status === "completed"
                        ? "bg-accent/20 text-accent"
                        : "bg-light-text/10 text-light-text/50"
                  }`}
                >
                  {goal.status}
                </span>
                {goal.plan && (
                  <button
                    onClick={() =>
                      setExpandedPlans((prev) => {
                        const next = new Set(prev);
                        if (next.has(goal.id)) next.delete(goal.id);
                        else next.add(goal.id);
                        return next;
                      })
                    }
                    className="flex items-center gap-1 text-xs text-light-text/50 hover:text-light-text/70"
                    aria-expanded={expandedPlans.has(goal.id)}
                    aria-label="Toggle plan"
                  >
                    <span
                      className={`inline-block transition-transform ${
                        expandedPlans.has(goal.id) ? "rotate-90" : ""
                      }`}
                    >
                      ▶
                    </span>
                    Plan
                  </button>
                )}
              </div>

              {/* Collapsible plan */}
              {goal.plan && expandedPlans.has(goal.id) && (
                <div className="prose prose-sm prose-invert mt-3 max-w-none rounded-lg bg-dark-bg p-3">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{goal.plan}</ReactMarkdown>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
