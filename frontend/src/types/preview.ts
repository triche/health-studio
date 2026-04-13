export interface TrendPoint {
  date: string;
  value: number;
}

export interface PreviewGoal {
  entity_type: "goal";
  entity_id: string;
  title: string;
  status: string;
  progress: number;
  target_value: number;
  current_value: number;
  deadline: string | null;
}

export interface PreviewMetricType {
  entity_type: "metric_type";
  entity_id: string;
  title: string;
  unit: string;
  latest_value: number | null;
  latest_date: string | null;
  trend: TrendPoint[];
}

export interface PreviewExerciseType {
  entity_type: "exercise_type";
  entity_id: string;
  title: string;
  category: string;
  result_unit: string;
  pr_value: number | null;
  pr_date: string | null;
  recent_results: TrendPoint[];
}

export type EntityPreviewData = PreviewGoal | PreviewMetricType | PreviewExerciseType;
