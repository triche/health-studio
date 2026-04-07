import { api } from "./client";
import type { Backlink, EntityNames, Mention } from "../types/mention";

const BACKLINK_PATHS: Record<string, string> = {
  goal: "goals",
  metric_type: "metric-types",
  exercise_type: "exercise-types",
};

export function getEntityNames(): Promise<EntityNames> {
  return api.get<EntityNames>("/api/entities/names");
}

export function getJournalMentions(journalId: string): Promise<Mention[]> {
  return api.get<Mention[]>(`/api/journals/${encodeURIComponent(journalId)}/mentions`);
}

export function getBacklinks(entityType: string, entityId: string): Promise<Backlink[]> {
  const path = BACKLINK_PATHS[entityType] ?? entityType;
  return api.get<Backlink[]>(`/api/${path}/${encodeURIComponent(entityId)}/backlinks`);
}
