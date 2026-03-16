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

// --- Games API ---

export type Genre = {
  id: string;
  name: string;
  description: string;
  difficulty_options: string[];
  icon: string;
};

export type GameStatus = "queued" | "generating" | "ready" | "failed";

export type Game = {
  id: string;
  owner_user_id: string;
  genre: string;
  title: string;
  pitch: string | null;
  prompt: string | null;
  visibility: string;
  play_count: number;
  status: GameStatus;
  status_message: string | null;
  created_at: string;
  updated_at: string;
};

export type GameCreated = {
  game_id: string;
  status: string;
  message: string;
  status_url: string;
};

export type GameStatusInfo = {
  game_id: string;
  status: GameStatus;
  status_message: string | null;
};

export type GameVersion = {
  id: string;
  game_id: string;
  version: number;
  blueprint_json: Record<string, unknown> | null;
  source_code: string | null;
  created_at: string;
};

export type GameList = {
  games: Game[];
  total: number;
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

    updateMe: (data: { username?: string; current_password?: string; new_password?: string }) =>
      request<User>("/api/auth/me", {
        method: "PATCH",
        body: data,
      }),
  },

  users: {
    getProfile: (username: string) =>
      request<User>(`/api/users/${encodeURIComponent(username)}`),
  },

  games: {
    genres: () => request<Genre[]>("/api/games/genres"),

    create: (data: { genre: string; title: string; prompt: string; difficulty?: string }) =>
      request<GameCreated>("/api/games", { method: "POST", body: data }),

    list: (limit = 20, offset = 0) =>
      request<GameList>(`/api/games?limit=${limit}&offset=${offset}`),

    get: (id: string) => request<Game>(`/api/games/${id}`),

    status: (id: string) => request<GameStatusInfo>(`/api/games/${id}/status`),

    versions: (id: string) => request<GameVersion[]>(`/api/games/${id}/versions`),

    delete: (id: string) => request<void>(`/api/games/${id}`, { method: "DELETE" }),
  },

  health: () => request<{ status: string }>("/api/health"),
};

export { ApiError };
