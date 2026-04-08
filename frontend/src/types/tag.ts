export interface TagCount {
  tag: string;
  count: number;
}

export interface TagEntity {
  entity_type: string;
  entity_id: string;
  title: string;
}

export interface TagEntitiesResponse {
  tag: string;
  entities: TagEntity[];
}
