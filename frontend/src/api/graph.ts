import { api } from "./client";
import type { GraphResponse } from "../types/graph";

export function getGraph(params?: {
  min_connections?: number;
  include_orphans?: boolean;
}): Promise<GraphResponse> {
  const search = new URLSearchParams();
  if (params?.min_connections !== undefined)
    search.set("min_connections", String(params.min_connections));
  if (params?.include_orphans !== undefined)
    search.set("include_orphans", String(params.include_orphans));
  const qs = search.toString();
  return api.get<GraphResponse>(`/api/graph${qs ? `?${qs}` : ""}`);
}
