const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type ApiError = {
  detail?: string;
  message: string;
};

export type HealthResponse = {
  ok: boolean;
};

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;

    try {
      const data = (await response.json()) as ApiError;
      if (typeof data.detail === "string" && data.detail.length > 0) {
        errorMessage = data.detail;
      } else if (typeof data.message === "string" && data.message.length > 0) {
        errorMessage = data.message;
      }
    } catch {
      // Preserve fallback message when the response is not JSON.
    }

    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health");
}
