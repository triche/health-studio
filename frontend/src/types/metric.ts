export interface MetricType {
  id: string;
  name: string;
  unit: string;
  created_at: string;
}

export interface MetricEntry {
  id: string;
  metric_type_id: string;
  value: number;
  recorded_date: string;
  notes: string | null;
  created_at: string;
}

export interface MetricEntryListResponse {
  items: MetricEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface MetricEntryCreate {
  metric_type_id: string;
  value: number;
  recorded_date: string;
  notes?: string;
}

export interface MetricTypeCreate {
  name: string;
  unit: string;
}

export interface TrendPoint {
  recorded_date: string;
  value: number;
}

export interface TrendResponse {
  metric_type_id: string;
  metric_name: string;
  unit: string;
  data: TrendPoint[];
}
