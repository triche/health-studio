export interface TimelineItem {
  type: "journal" | "metric" | "result" | "goal";
  id: string;
  title: string;
  summary: string;
  date: string;
  tags: string[];
  metadata: Record<string, unknown>;
}

export interface TimelineResponse {
  items: TimelineItem[];
  total: number;
  page: number;
  per_page: number;
}
