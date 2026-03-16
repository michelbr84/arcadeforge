"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { api, ApiError } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading, fetchUser } = useAuthStore();

  // Username form
  const [username, setUsername] = useState("");
  const [usernameMsg, setUsernameMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [usernameSaving, setUsernameSaving] = useState(false);

  // Password form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [passwordSaving, setPasswordSaving] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
    }
  }, [user]);

  if (loading || !user) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </main>
    );
  }

  async function handleUsernameSubmit(e: React.FormEvent) {
    e.preventDefault();
    setUsernameMsg(null);
    setUsernameSaving(true);
    try {
      await api.auth.updateMe({ username });
      await fetchUser();
      setUsernameMsg({ type: "success", text: "Username updated." });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to update username.";
      setUsernameMsg({ type: "error", text: message });
    } finally {
      setUsernameSaving(false);
    }
  }

  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPasswordMsg(null);
    setPasswordSaving(true);
    try {
      await api.auth.updateMe({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setPasswordMsg({ type: "success", text: "Password updated." });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to update password.";
      setPasswordMsg({ type: "error", text: message });
    } finally {
      setPasswordSaving(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-2xl font-bold mb-8">Settings</h1>

      {/* Username */}
      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Username</h2>
        <form onSubmit={handleUsernameSubmit} className="space-y-4">
          {usernameMsg && (
            <div
              className={`rounded-lg px-4 py-3 text-sm ${
                usernameMsg.type === "success"
                  ? "bg-green-500/10 border border-green-500/20 text-green-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}
            >
              {usernameMsg.text}
            </div>
          )}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value.toLowerCase())}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Your profile will be visible at /@{username}
            </p>
          </div>
          <button
            type="submit"
            disabled={usernameSaving || username === user.username}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {usernameSaving ? "Saving..." : "Update username"}
          </button>
        </form>
      </section>

      {/* Password */}
      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <h2 className="text-lg font-semibold mb-4">Change password</h2>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          {passwordMsg && (
            <div
              className={`rounded-lg px-4 py-3 text-sm ${
                passwordMsg.type === "success"
                  ? "bg-green-500/10 border border-green-500/20 text-green-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}
            >
              {passwordMsg.text}
            </div>
          )}
          <div>
            <label htmlFor="current-password" className="block text-sm font-medium text-gray-300 mb-1">
              Current password
            </label>
            <input
              id="current-password"
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="new-password" className="block text-sm font-medium text-gray-300 mb-1">
              New password
            </label>
            <input
              id="new-password"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-500">At least 8 characters.</p>
          </div>
          <button
            type="submit"
            disabled={passwordSaving || !currentPassword || !newPassword}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {passwordSaving ? "Updating..." : "Change password"}
          </button>
        </form>
      </section>
    </main>
  );
}
