export interface Goal {
  id: string;
  title: string;
  description: string;
  plan: string;
  target_type: string;
  target_id: string;
  target_value: number;
  start_value: number | null;
  current_value: number;
  lower_is_better: boolean;
  status: string;
  deadline: string | null;
  progress: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface GoalListResponse {
  items: Goal[];
  total: number;
  page: number;
  per_page: number;
}

export interface GoalCreate {
  title: string;
  description?: string;
  plan?: string;
  target_type: string;
  target_id: string;
  target_value: number;
  start_value?: number;
  lower_is_better?: boolean;
  status?: string;
  deadline?: string;
  tags?: string[];
}

export interface GoalUpdate {
  title?: string;
  description?: string;
  plan?: string;
  target_type?: string;
  target_id?: string;
  target_value?: number;
  start_value?: number | null;
  lower_is_better?: boolean;
  status?: string;
  deadline?: string | null;
  tags?: string[];
}
