import { api } from "./client";
import type {
  JournalCreate,
  JournalEntry,
  JournalListResponse,
  JournalUpdate,
} from "../types/journal";

export function listJournals(params?: {
  page?: number;
  per_page?: number;
  date_from?: string;
  date_to?: string;
}): Promise<JournalListResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.per_page) search.set("per_page", String(params.per_page));
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<JournalListResponse>(`/api/journals${qs ? `?${qs}` : ""}`);
}

export function getJournal(id: string): Promise<JournalEntry> {
  return api.get<JournalEntry>(`/api/journals/${encodeURIComponent(id)}`);
}

export function createJournal(data: JournalCreate): Promise<JournalEntry> {
  return api.post<JournalEntry>("/api/journals", data);
}

export function updateJournal(id: string, data: JournalUpdate): Promise<JournalEntry> {
  return api.put<JournalEntry>(`/api/journals/${encodeURIComponent(id)}`, data);
}

export function deleteJournal(id: string): Promise<void> {
  return api.delete(`/api/journals/${encodeURIComponent(id)}`);
}
