import { api } from "./client";
import type {
  ExerciseType,
  ExerciseTypeCreate,
  ResultEntry,
  ResultEntryCreate,
  ResultEntryUpdate,
  ResultEntryListResponse,
  ResultTrendResponse,
} from "../types/result";

export function listExerciseTypes(params?: { tag?: string }): Promise<ExerciseType[]> {
  const search = new URLSearchParams();
  if (params?.tag) search.set("tag", params.tag);
  const qs = search.toString();
  return api.get<ExerciseType[]>(`/api/exercise-types${qs ? `?${qs}` : ""}`);
}

export function createExerciseType(data: ExerciseTypeCreate): Promise<ExerciseType> {
  return api.post<ExerciseType>("/api/exercise-types", data);
}

export function deleteExerciseType(id: string): Promise<void> {
  return api.delete(`/api/exercise-types/${encodeURIComponent(id)}`);
}

export function listResultEntries(params?: {
  page?: number;
  per_page?: number;
  exercise_type_id?: string;
  date_from?: string;
  date_to?: string;
}): Promise<ResultEntryListResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.per_page) search.set("per_page", String(params.per_page));
  if (params?.exercise_type_id) search.set("exercise_type_id", params.exercise_type_id);
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<ResultEntryListResponse>(`/api/results${qs ? `?${qs}` : ""}`);
}

export function createResultEntry(data: ResultEntryCreate): Promise<ResultEntry> {
  return api.post<ResultEntry>("/api/results", data);
}

export function updateResultEntry(id: string, data: ResultEntryUpdate): Promise<ResultEntry> {
  return api.put<ResultEntry>(`/api/results/${encodeURIComponent(id)}`, data);
}

export function deleteResultEntry(id: string): Promise<void> {
  return api.delete(`/api/results/${encodeURIComponent(id)}`);
}

export function getResultTrend(
  exerciseTypeId: string,
  params?: { date_from?: string; date_to?: string },
): Promise<ResultTrendResponse> {
  const search = new URLSearchParams();
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<ResultTrendResponse>(
    `/api/results/trends/${encodeURIComponent(exerciseTypeId)}${qs ? `?${qs}` : ""}`,
  );
}

export function getPRHistory(exerciseTypeId: string): Promise<ResultEntry[]> {
  return api.get<ResultEntry[]>(`/api/results/prs/${encodeURIComponent(exerciseTypeId)}`);
}
