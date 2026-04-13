import { api } from "./client";
import type { EntityPreviewData } from "../types/preview";

export function getEntityPreview(type: string, id: string): Promise<EntityPreviewData> {
  return api.get<EntityPreviewData>(
    `/api/entities/preview?type=${encodeURIComponent(type)}&id=${encodeURIComponent(id)}`,
  );
}
