import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../api/dashboard";
import type { DashboardSummary } from "../types/dashboard";

function formatDuration(totalMinutes: number): string {
  const h = Math.floor(totalMinutes / 60);
  const m = Math.round(totalMinutes % 60);
  return `${h}h ${m}m`;
}

function formatTime(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.round(totalSeconds % 60);
  const parts: string[] = [];
  if (h > 0) parts.push(`${h}h`);
  if (m > 0) parts.push(`${m}m`);
  if (s > 0 || parts.length === 0) parts.push(`${s}s`);
  return parts.join(" ");
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Failed to load dashboard"));
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="rounded-lg bg-red-500/20 p-3 text-sm text-red-400">{error}</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <p className="text-light-text/50">Loading...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-light-text">Dashboard</h1>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Journal Entries */}
        <div className="rounded-lg bg-dark-surface p-4">
          <h2 className="mb-3 text-lg font-semibold text-light-text">Recent Journal Entries</h2>
          {summary.recent_journals.length === 0 ? (
            <p className="text-sm text-light-text/50">No recent journal entries</p>
          ) : (
            <ul className="space-y-2">
              {summary.recent_journals.map((j) => (
                <li key={j.id}>
                  <Link
                    to={`/journals/${j.id}`}
                    className="block rounded-lg px-3 py-2 text-sm text-light-text hover:bg-dark-bg"
                  >
                    <span className="font-medium">{j.title}</span>
                    <span className="ml-2 text-xs text-light-text/50">{j.entry_date}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Active Goals */}
        <div className="rounded-lg bg-dark-surface p-4">
          <h2 className="mb-3 text-lg font-semibold text-light-text">Active Goals</h2>
          {summary.active_goals.length === 0 ? (
            <p className="text-sm text-light-text/50">No active goals</p>
          ) : (
            <ul className="space-y-3">
              {summary.active_goals.map((g) => (
                <li key={g.id}>
                  <Link to="/goals" className="block rounded-lg px-3 py-2 hover:bg-dark-bg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-light-text">{g.title}</span>
                      <span className="text-xs text-light-text/70">{Math.round(g.progress)}%</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-dark-bg">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(100, g.progress)}%` }}
                      />
                    </div>
                    {g.deadline && (
                      <span className="mt-1 text-xs text-light-text/50">Due: {g.deadline}</span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Latest Metrics */}
        <div className="rounded-lg bg-dark-surface p-4">
          <h2 className="mb-3 text-lg font-semibold text-light-text">Latest Metrics</h2>
          {summary.latest_metrics.length === 0 ? (
            <p className="text-sm text-light-text/50">No metrics recorded</p>
          ) : (
            <ul className="space-y-2">
              {summary.latest_metrics.map((m) => (
                <li
                  key={m.metric_type_id}
                  className="flex items-center justify-between rounded-lg px-3 py-2"
                >
                  <span className="text-sm text-light-text">{m.metric_name}</span>
                  <span className="text-sm font-medium text-light-text">
                    {m.unit === "minutes" && m.value >= 60 ? formatDuration(m.value) : m.value}{" "}
                    <span className="text-xs text-light-text/50">
                      {m.unit === "minutes" && m.value >= 60 ? "" : m.unit}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Recent PRs */}
        <div className="rounded-lg bg-dark-surface p-4">
          <h2 className="mb-3 text-lg font-semibold text-light-text">Recent PRs</h2>
          {summary.recent_prs.length === 0 ? (
            <p className="text-sm text-light-text/50">No recent PRs</p>
          ) : (
            <ul className="space-y-2">
              {summary.recent_prs.map((pr) => (
                <li key={pr.id} className="flex items-center justify-between rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-block rounded bg-yellow-500/20 px-1.5 py-0.5 text-xs font-bold text-yellow-400">
                      PR
                    </span>
                    <span className="text-sm text-light-text">{pr.exercise_name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-light-text">
                      {pr.display_value ||
                        (pr.result_unit === "seconds" || pr.result_unit === "time"
                          ? formatTime(pr.value)
                          : pr.value)}
                    </span>
                    <span className="ml-2 text-xs text-light-text/50">{pr.recorded_date}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
