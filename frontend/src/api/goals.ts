import { api } from "./client";
import type { Goal, GoalCreate, GoalUpdate, GoalListResponse } from "../types/goal";

export function listGoals(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  tag?: string;
}): Promise<GoalListResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.per_page) search.set("per_page", String(params.per_page));
  if (params?.status) search.set("status", params.status);
  if (params?.tag) search.set("tag", params.tag);
  const qs = search.toString();
  return api.get<GoalListResponse>(`/api/goals${qs ? `?${qs}` : ""}`);
}

export function getGoal(id: string): Promise<Goal> {
  return api.get<Goal>(`/api/goals/${encodeURIComponent(id)}`);
}

export function createGoal(data: GoalCreate): Promise<Goal> {
  return api.post<Goal>("/api/goals", data);
}

export function updateGoal(id: string, data: GoalUpdate): Promise<Goal> {
  return api.put<Goal>(`/api/goals/${encodeURIComponent(id)}`, data);
}

export function deleteGoal(id: string): Promise<void> {
  return api.delete(`/api/goals/${encodeURIComponent(id)}`);
}
