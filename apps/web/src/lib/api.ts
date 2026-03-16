/**
 * API client for ArcadeForge backend.
 *
 * All requests include credentials (cookies) for session auth.
 * Base URL defaults to localhost:8000 in development.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    const message = typeof data === "object" && data !== null && "detail" in data
      ? String((data as { detail: string }).detail)
      : `API error ${status}`;
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(res.status, data);
  }

  return data as T;
}

// --- Auth API ---

export type User = {
  id: string;
  email: string;
  username: string;
  status: string;
  created_at: string;
  email_verified_at: string | null;
};

export const api = {
  auth: {
    register: (email: string, username: string, password: string) =>
      request<User>("/api/auth/register", {
        method: "POST",
        body: { email, username, password },
      }),

    login: (email: string, password: string) =>
      request<User>("/api/auth/login", {
        method: "POST",
        body: { email, password },
      }),

    logout: () =>
      request<{ message: string }>("/api/auth/logout", { method: "POST" }),

    me: () => request<User>("/api/auth/me"),
  },

  health: () => request<{ status: string }>("/api/health"),
};

export { ApiError };
