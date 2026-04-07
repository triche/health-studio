export interface Mention {
  entity_type: string;
  entity_id: string;
  display_text: string;
}

export interface Backlink {
  journal_id: string;
  title: string;
  entry_date: string;
  snippet: string;
}

export interface EntityNameItem {
  id: string;
  name: string;
}

export interface EntityNames {
  goals: EntityNameItem[];
  metric_types: EntityNameItem[];
  exercise_types: EntityNameItem[];
}
