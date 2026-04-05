const BASE_HEADERS: Record<string, string> = {
  "X-Requested-With": "HealthStudio",
};

export type CsvEntity =
  | "metric_types"
  | "metric_entries"
  | "exercise_types"
  | "result_entries"
  | "journal_entries"
  | "goals";

export type CsvImportEntity = "metric_entries" | "result_entries";

export interface ImportResult {
  [key: string]: number;
}

async function fetchBlob(url: string): Promise<Blob> {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: BASE_HEADERS,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Export failed: ${response.status}`);
  }
  return response.blob();
}

export function exportJson(): Promise<Blob> {
  return fetchBlob("/api/export/json");
}

export function exportCsv(entity: CsvEntity): Promise<Blob> {
  return fetchBlob(`/api/export/csv/${encodeURIComponent(entity)}`);
}

export function exportJournalsMarkdown(): Promise<Blob> {
  return fetchBlob("/api/export/journals/markdown");
}

export async function importJson(data: unknown): Promise<ImportResult> {
  const response = await fetch("/api/import/json", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      ...BASE_HEADERS,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Import failed: ${response.status}`);
  }
  return response.json();
}

export async function importCsv(entity: CsvImportEntity, file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`/api/import/csv/${encodeURIComponent(entity)}`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "HealthStudio",
    },
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Import failed: ${response.status}`);
  }
  return response.json();
}
