import { api } from "./client";
import type { DashboardSummary } from "../types/dashboard";

export function getDashboardSummary(): Promise<DashboardSummary> {
  return api.get<DashboardSummary>("/api/dashboard/summary");
}
