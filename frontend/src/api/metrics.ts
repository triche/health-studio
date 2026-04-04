import { api } from "./client";
import type {
  MetricType,
  MetricTypeCreate,
  MetricEntry,
  MetricEntryCreate,
  MetricEntryUpdate,
  MetricEntryListResponse,
  TrendResponse,
} from "../types/metric";

export function listMetricTypes(): Promise<MetricType[]> {
  return api.get<MetricType[]>("/api/metric-types");
}

export function createMetricType(data: MetricTypeCreate): Promise<MetricType> {
  return api.post<MetricType>("/api/metric-types", data);
}

export function deleteMetricType(id: string): Promise<void> {
  return api.delete(`/api/metric-types/${encodeURIComponent(id)}`);
}

export function listMetricEntries(params?: {
  page?: number;
  per_page?: number;
  metric_type_id?: string;
  date_from?: string;
  date_to?: string;
}): Promise<MetricEntryListResponse> {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.per_page) search.set("per_page", String(params.per_page));
  if (params?.metric_type_id) search.set("metric_type_id", params.metric_type_id);
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<MetricEntryListResponse>(`/api/metrics${qs ? `?${qs}` : ""}`);
}

export function createMetricEntry(data: MetricEntryCreate): Promise<MetricEntry> {
  return api.post<MetricEntry>("/api/metrics", data);
}

export function updateMetricEntry(id: string, data: MetricEntryUpdate): Promise<MetricEntry> {
  return api.put<MetricEntry>(`/api/metrics/${encodeURIComponent(id)}`, data);
}

export function deleteMetricEntry(id: string): Promise<void> {
  return api.delete(`/api/metrics/${encodeURIComponent(id)}`);
}

export function getMetricTrend(
  metricTypeId: string,
  params?: { date_from?: string; date_to?: string },
): Promise<TrendResponse> {
  const search = new URLSearchParams();
  if (params?.date_from) search.set("date_from", params.date_from);
  if (params?.date_to) search.set("date_to", params.date_to);
  const qs = search.toString();
  return api.get<TrendResponse>(
    `/api/metrics/trends/${encodeURIComponent(metricTypeId)}${qs ? `?${qs}` : ""}`,
  );
}
