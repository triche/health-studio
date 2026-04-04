export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  entry_date: string;
  created_at: string;
  updated_at: string;
}

export interface JournalListResponse {
  items: JournalEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface JournalCreate {
  title: string;
  content: string;
  entry_date: string;
}

export interface JournalUpdate {
  title?: string;
  content?: string;
  entry_date?: string;
}
