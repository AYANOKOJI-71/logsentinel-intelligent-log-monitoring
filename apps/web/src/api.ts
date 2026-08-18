import type { Alert, AlertStatus, Overview } from "./types";

const endpoint = import.meta.env.LOGWATCH_API_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${endpoint}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  overview: () => request<Overview>("/api/overview"),
  seedDemo: () => request("/api/demo/seed", { method: "POST" }),
  updateAlert: (id: string, status: AlertStatus) =>
    request<Alert>(`/api/alerts/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
};
