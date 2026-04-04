const BASE_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  "X-Requested-With": "HealthStudio",
};

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...BASE_HEADERS,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  get<T>(url: string): Promise<T> {
    return request<T>(url, { method: "GET" });
  },

  post<T>(url: string, data: unknown): Promise<T> {
    return request<T>(url, { method: "POST", body: JSON.stringify(data) });
  },

  put<T>(url: string, data: unknown): Promise<T> {
    return request<T>(url, { method: "PUT", body: JSON.stringify(data) });
  },

  delete(url: string): Promise<void> {
    return request<void>(url, { method: "DELETE" });
  },
};
