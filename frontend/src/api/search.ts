import { api } from "./client";
import type { SearchResponse } from "../types/search";

export function search(
  query: string,
  types?: string,
  limit?: number,
  offset?: number,
): Promise<SearchResponse> {
  const params = new URLSearchParams();
  params.set("q", query);
  if (types) params.set("types", types);
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));
  return api.get<SearchResponse>(`/api/search?${params.toString()}`);
}
