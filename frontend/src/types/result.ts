export interface ExerciseType {
  id: string;
  name: string;
  category: string;
  result_unit: string;
  tags: string[];
  created_at: string;
}

export interface ResultEntry {
  id: string;
  exercise_type_id: string;
  value: number;
  display_value: string | null;
  recorded_date: string;
  is_pr: boolean;
  is_rx: boolean;
  notes: string | null;
  created_at: string;
}

export interface ResultEntryListResponse {
  items: ResultEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface ExerciseTypeCreate {
  name: string;
  category: string;
  result_unit: string;
  tags?: string[];
}

export interface ResultEntryCreate {
  exercise_type_id: string;
  value: number;
  recorded_date: string;
  display_value?: string;
  is_rx?: boolean;
  notes?: string;
}

export interface ResultEntryUpdate {
  value?: number;
  recorded_date?: string;
  display_value?: string;
  is_rx?: boolean;
  notes?: string;
}

export interface ResultTrendPoint {
  recorded_date: string;
  value: number;
  is_pr: boolean;
  is_rx: boolean;
}

export interface ResultTrendResponse {
  exercise_type_id: string;
  exercise_name: string;
  result_unit: string;
  data: ResultTrendPoint[];
}
