export interface SearchResult {
  entity_type: string;
  entity_id: string;
  title: string;
  snippet: string;
  rank: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}
