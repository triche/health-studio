import { api } from "./client";

export interface AuthStatus {
  registered: boolean;
  authenticated: boolean;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  prefix: string;
  raw_key: string;
  created_at: string;
}

export function getAuthStatus(): Promise<AuthStatus> {
  return api.get<AuthStatus>("/api/auth/status");
}

export function beginRegistration(displayName: string): Promise<{ options: string }> {
  return api.post<{ options: string }>("/api/auth/register", {
    display_name: displayName,
  });
}

export function completeRegistration(
  credential: unknown,
): Promise<{ id: number; display_name: string }> {
  return api.post<{ id: number; display_name: string }>("/api/auth/register/complete", credential);
}

export function beginLogin(): Promise<{ options: string }> {
  return api.post<{ options: string }>("/api/auth/login", {});
}

export function completeLogin(credential: unknown): Promise<{ status: string }> {
  return api.post<{ status: string }>("/api/auth/login/complete", credential);
}

export function logout(): Promise<{ status: string }> {
  return api.post<{ status: string }>("/api/auth/logout", {});
}

export function listApiKeys(): Promise<ApiKeyInfo[]> {
  return api.get<ApiKeyInfo[]>("/api/keys");
}

export function createApiKey(name: string): Promise<ApiKeyCreated> {
  return api.post<ApiKeyCreated>("/api/keys", { name });
}

export function revokeApiKey(id: string): Promise<void> {
  return api.delete(`/api/keys/${encodeURIComponent(id)}`);
}
