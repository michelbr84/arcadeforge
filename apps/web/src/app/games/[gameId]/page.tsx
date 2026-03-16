"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type Game, type GameVersion, ApiError } from "@/lib/api";

export default function GameDetailPage() {
  const params = useParams();
  const gameId = params.gameId as string;

  const [game, setGame] = useState<Game | null>(null);
  const [versions, setVersions] = useState<GameVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "code">("overview");

  useEffect(() => {
    if (!gameId) return;

    setLoading(true);
    Promise.all([
      api.games.get(gameId),
      api.games.versions(gameId).catch(() => []),
    ])
      .then(([gameData, versionsData]) => {
        setGame(gameData);
        setVersions(versionsData);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load game.");
      })
      .finally(() => setLoading(false));
  }, [gameId]);

  if (loading) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 text-lg">Loading game...</p>
          <p className="text-gray-600 text-sm mt-2">Generation may still be in progress.</p>
        </div>
      </main>
    );
  }

  if (error || !game) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center">
        <h1 className="text-2xl font-bold text-gray-400">{error || "Game not found"}</h1>
        <Link href="/dashboard" className="text-indigo-400 hover:text-indigo-300 text-sm mt-4">
          Back to dashboard
        </Link>
      </main>
    );
  }

  const latestVersion = versions.length > 0 ? versions[0] : null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{game.title}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-400">
            <span className="rounded-full bg-gray-800 px-3 py-0.5 capitalize">{game.genre}</span>
            <span>{game.play_count} plays</span>
            <span>{game.visibility}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-800 mb-6">
        <div className="flex gap-6">
          {(["overview", "code"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-medium capitalize transition-colors ${
                activeTab === tab
                  ? "border-b-2 border-indigo-500 text-white"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {game.pitch && (
            <section>
              <h2 className="text-sm font-medium text-gray-400 mb-2">Description</h2>
              <p className="text-gray-200">{game.pitch}</p>
            </section>
          )}

          {game.prompt && (
            <section>
              <h2 className="text-sm font-medium text-gray-400 mb-2">Original Prompt</h2>
              <div className="rounded-lg bg-gray-900 border border-gray-800 p-4 text-sm text-gray-300">
                {game.prompt}
              </div>
            </section>
          )}

          <section>
            <h2 className="text-sm font-medium text-gray-400 mb-2">Versions</h2>
            {versions.length === 0 ? (
              <div className="rounded-lg bg-gray-900 border border-gray-800 p-6 text-center text-gray-500">
                No versions yet. Generation may still be in progress.
              </div>
            ) : (
              <div className="space-y-2">
                {versions.map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center justify-between rounded-lg bg-gray-900 border border-gray-800 px-4 py-3"
                  >
                    <span className="text-sm font-medium">v{v.version}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {activeTab === "code" && (
        <div>
          {latestVersion?.source_code ? (
            <pre className="rounded-lg bg-gray-900 border border-gray-800 p-4 text-sm text-gray-300 overflow-x-auto whitespace-pre-wrap">
              {latestVersion.source_code}
            </pre>
          ) : (
            <div className="rounded-lg bg-gray-900 border border-gray-800 p-8 text-center text-gray-500">
              No code available yet. Generation may still be in progress.
            </div>
          )}
        </div>
      )}
    </main>
  );
}
