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

  // LLM settings form
  const [llmProvider, setLlmProvider] = useState("");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [llmKeySet, setLlmKeySet] = useState(false);
  const [llmMsg, setLlmMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [llmSaving, setLlmSaving] = useState(false);

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

  // Load LLM settings on mount
  useEffect(() => {
    api.auth.getLLMSettings().then((s) => {
      setLlmProvider(s.llm_provider || "");
      setLlmModel(s.llm_model || "");
      setLlmKeySet(s.llm_api_key_set);
    }).catch(() => {});
  }, []);

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

  async function handleLLMSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLlmSaving(true);
    setLlmMsg(null);
    try {
      const payload: Record<string, string | null> = {
        llm_provider: llmProvider || null,
        llm_model: llmModel || null,
      };
      if (llmApiKey) {
        payload.llm_api_key = llmApiKey;
      }
      const result = await api.auth.updateLLMSettings(payload);
      setLlmKeySet(result.llm_api_key_set);
      setLlmApiKey("");
      setLlmMsg({ type: "success", text: "LLM settings saved successfully." });
    } catch {
      setLlmMsg({ type: "error", text: "Failed to save LLM settings." });
    } finally {
      setLlmSaving(false);
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
      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 mb-6">
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

      {/* AI Game Generation */}
      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <h2 className="text-lg font-semibold text-white mb-1">AI Game Generation</h2>
        <p className="text-sm text-gray-400 mb-4">
          Connect your LLM API key to generate games from your prompts using AI.
          Without a key, games use built-in templates.
        </p>

        {llmMsg && (
          <div className={`rounded-lg px-4 py-2 text-sm mb-4 ${
            llmMsg.type === "success" ? "bg-green-900/50 text-green-300" : "bg-red-900/50 text-red-300"
          }`}>{llmMsg.text}</div>
        )}

        <form onSubmit={handleLLMSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
            <select
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="">Select a provider...</option>
              <option value="openrouter">OpenRouter</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic (Claude)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              API Key {llmKeySet && <span className="text-green-400 text-xs ml-2">configured</span>}
            </label>
            <input
              type="password"
              value={llmApiKey}
              onChange={(e) => setLlmApiKey(e.target.value)}
              placeholder={llmKeySet ? "Enter new key to change..." : "sk-..."}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Model</label>
            <input
              type="text"
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              placeholder={
                llmProvider === "anthropic" ? "claude-sonnet-4-20250514" :
                llmProvider === "openai" ? "gpt-4o" :
                llmProvider === "openrouter" ? "openai/gpt-4o" :
                "Select a provider first"
              }
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={llmSaving || !llmProvider}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {llmSaving ? "Saving..." : "Save LLM Settings"}
          </button>
        </form>
      </section>
    </main>
  );
}
