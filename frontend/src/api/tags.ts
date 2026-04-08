import { api } from "./client";
import type { TagCount, TagEntitiesResponse } from "../types/tag";

export function listTags(): Promise<TagCount[]> {
  return api.get<TagCount[]>("/api/tags");
}

export function getEntitiesByTag(tag: string, type?: string): Promise<TagEntitiesResponse> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  const qs = params.toString();
  return api.get<TagEntitiesResponse>(`/api/tags/${encodeURIComponent(tag)}${qs ? `?${qs}` : ""}`);
}
