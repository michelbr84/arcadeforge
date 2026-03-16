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

export type ValidationRun = {
  id: string;
  game_version_id: string;
  status: string;
  scan_passed: boolean | null;
  report_json_path: string | null;
  screenshot_path: string | null;
  created_at: string;
  completed_at: string | null;
};

export type ScanResult = {
  passed: boolean;
  findings: { line: number; pattern: string; severity: string; message: string }[];
  critical_count: number;
  high_count: number;
};

export type PlaySessionCreated = {
  session_id: string;
  status: string;
  message: string;
  ws_url: string | null;
};

export type PlaySessionInfo = {
  id: string;
  game_version_id: string;
  status: string;
  ws_url: string | null;
  sandbox_ref: string | null;
  created_at: string;
  expires_at: string;
};

export type ArcadeGame = Game & {
  owner_username: string | null;
};

export type ArcadeGameList = {
  games: ArcadeGame[];
  total: number;
  query: string;
  genre: string;
  sort: string;
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

    createVersion: (id: string, sourceCode: string) =>
      request<GameVersion>(`/api/games/${id}/versions`, {
        method: "POST",
        body: { source_code: sourceCode },
      }),

    delete: (id: string) => request<void>(`/api/games/${id}`, { method: "DELETE" }),

    play: (id: string) =>
      request<PlaySessionCreated>(`/api/games/${id}/play`, { method: "POST" }),

    playSession: (gameId: string, sessionId: string) =>
      request<PlaySessionInfo>(`/api/games/${gameId}/play/${sessionId}`),

    stopPlay: (gameId: string, sessionId: string) =>
      request<{ message: string }>(`/api/games/${gameId}/play/${sessionId}/stop`, { method: "POST" }),

    validate: (id: string) =>
      request<{ validation_id: string; status: string; message: string }>(
        `/api/games/${id}/validate`,
        { method: "POST" },
      ),

    validations: (id: string) =>
      request<ValidationRun[]>(`/api/games/${id}/validations`),

    scan: (id: string) => request<ScanResult>(`/api/games/${id}/scan`),
  },

  arcade: {
    games: (params?: { q?: string; genre?: string; sort?: string; limit?: number; offset?: number }) => {
      const p = new URLSearchParams();
      if (params?.q) p.set("q", params.q);
      if (params?.genre) p.set("genre", params.genre);
      if (params?.sort) p.set("sort", params.sort);
      if (params?.limit) p.set("limit", String(params.limit));
      if (params?.offset) p.set("offset", String(params.offset));
      const qs = p.toString();
      return request<ArcadeGameList>(`/api/arcade/games${qs ? `?${qs}` : ""}`);
    },
  },

  health: () => request<{ status: string }>("/api/health"),
};

export { ApiError };
