export interface GraphNode {
  id: string;
  type: "journal" | "metric_type" | "exercise_type" | "goal";
  label: string;
  tags: string[];
  date?: string;
  status?: string;
  progress?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "mentions" | "tracks" | "shared_tag";
  tag?: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
