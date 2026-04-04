export interface DashboardJournal {
  id: string;
  title: string;
  entry_date: string;
}

export interface DashboardGoal {
  id: string;
  title: string;
  target_type: string;
  target_value: number;
  current_value: number;
  progress: number;
  status: string;
  deadline: string | null;
}

export interface DashboardMetric {
  metric_type_id: string;
  metric_name: string;
  unit: string;
  value: number;
  recorded_date: string;
}

export interface DashboardPR {
  id: string;
  exercise_name: string;
  value: number;
  display_value: string | null;
  result_unit: string | null;
  recorded_date: string;
  is_rx: boolean;
}

export interface DashboardSummary {
  recent_journals: DashboardJournal[];
  active_goals: DashboardGoal[];
  latest_metrics: DashboardMetric[];
  recent_prs: DashboardPR[];
}
