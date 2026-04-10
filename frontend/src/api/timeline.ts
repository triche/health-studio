import { api } from "./client";
import type { TimelineResponse } from "../types/timeline";

export function getTimeline(params?: {
  page?: number;
  per_page?: number;
  types?: string;
  tag?: string;
  date_from?: string;
  date_to?: string;
}): Promise<TimelineResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.per_page) search.set("per_page", String(params.per_page));
  if (params?.types) search.set("types", params.types);
  if (params?.tag) search.set("tag", params.tag);
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<TimelineResponse>(`/api/timeline${qs ? `?${qs}` : ""}`);
}
