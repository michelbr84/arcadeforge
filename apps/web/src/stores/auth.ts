/**
 * Auth state management with Zustand.
 *
 * Manages user session state and provides auth actions.
 */

import { create } from "zustand";
import { api, type User, ApiError } from "@/lib/api";

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;

  // Actions
  register: (email: string, username: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  error: null,

  register: async (email, username, password) => {
    set({ loading: true, error: null });
    try {
      const user = await api.auth.register(email, username, password);
      set({ user, loading: false });
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Registration failed.";
      set({ error: message, loading: false });
      throw e;
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const user = await api.auth.login(email, password);
      set({ user, loading: false });
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Login failed.";
      set({ error: message, loading: false });
      throw e;
    }
  },

  logout: async () => {
    try {
      await api.auth.logout();
    } catch {
      // Logout should succeed even if API call fails
    }
    set({ user: null });
  },

  fetchUser: async () => {
    set({ loading: true });
    try {
      const user = await api.auth.me();
      set({ user, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
