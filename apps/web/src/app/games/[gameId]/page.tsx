"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type Game, type GameVersion, type GameStatus, type ValidationRun, ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import GameCodeEditor from "@/components/GameCodeEditor";
import GamePlayerNoVNC from "@/components/GamePlayerNoVNC";

const settings_sandbox_ttl = 1800; // 30 minutes default

const STATUS_LABELS: Record<GameStatus, { label: string; color: string }> = {
  queued: { label: "Queued", color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" },
  generating: { label: "Generating...", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  ready: { label: "Ready", color: "bg-green-500/10 text-green-400 border-green-500/20" },
  failed: { label: "Failed", color: "bg-red-500/10 text-red-400 border-red-500/20" },
};

export default function GameDetailPage() {
  const params = useParams();
  const gameId = params.gameId as string;

  const currentUser = useAuthStore((s) => s.user);

  const [game, setGame] = useState<Game | null>(null);
  const [versions, setVersions] = useState<GameVersion[]>([]);
  const [validations, setValidations] = useState<ValidationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "play" | "code" | "validate">("overview");
  const [playSessionId, setPlaySessionId] = useState<string | null>(null);
  const [playWsUrl, setPlayWsUrl] = useState<string | null>(null);
  const [playLoading, setPlayLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [forking, setForking] = useState(false);

  const isOwner = currentUser?.id === game?.owner_user_id;

  async function handleFork() {
    if (forking || !gameId) return;
    setForking(true);
    try {
      const forked = await api.games.fork(gameId);
      window.location.href = `/games/${forked.id}`;
    } catch {
      setForking(false);
    }
  }

  const loadGame = useCallback(async () => {
    if (!gameId) return;
    try {
      const [gameData, versionsData, validationData] = await Promise.all([
        api.games.get(gameId),
        api.games.versions(gameId).catch(() => []),
        api.games.validations(gameId).catch(() => []),
      ]);
      setGame(gameData);
      setVersions(versionsData);
      setValidations(validationData);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load game.");
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  async function handleValidate() {
    if (!gameId || validating) return;
    setValidating(true);
    try {
      await api.games.validate(gameId);
      await loadGame();
    } catch {
      // Error handled via reload
    } finally {
      setValidating(false);
    }
  }

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  // Poll for status while generating
  useEffect(() => {
    if (!game || (game.status !== "queued" && game.status !== "generating")) return;

    const interval = setInterval(async () => {
      try {
        const status = await api.games.status(gameId);
        if (status.status !== game.status) {
          // Status changed — reload full data
          loadGame();
        }
      } catch {
        // Ignore poll errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [game, gameId, loadGame]);

  if (loading) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <p className="text-gray-400 text-lg">Loading game...</p>
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
  const statusInfo = STATUS_LABELS[game.status] || STATUS_LABELS.queued;
  const blueprint = latestVersion?.blueprint_json as Record<string, string | Record<string, string>> | null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{game.title}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm">
            <span className="rounded-full bg-gray-800 px-3 py-0.5 capitalize text-gray-300">{game.genre}</span>
            <span className={`rounded-full border px-3 py-0.5 ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
            <span className="text-gray-500">{game.play_count} plays</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {game.status === "ready" && (
            <button
              onClick={() => setActiveTab("play")}
              className="rounded-lg bg-green-600 px-5 py-2.5 font-medium text-white hover:bg-green-500 transition-colors"
            >
              Play
            </button>
          )}
          <button
            onClick={() => {
              navigator.clipboard.writeText(window.location.href);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500 transition-colors"
          >
            {copied ? "Copied!" : "Share"}
          </button>
          {game.visibility === "public" && !isOwner && (
            <button
              onClick={handleFork}
              disabled={forking}
              className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500 disabled:opacity-50 transition-colors"
            >
              {forking ? "Forking..." : "Fork"}
            </button>
          )}
        </div>
      </div>

      {/* Status banner for non-ready states */}
      {game.status === "generating" && (
        <div className="mb-6 rounded-lg bg-blue-500/10 border border-blue-500/20 px-4 py-3 text-sm text-blue-400">
          Game is being generated... This page will update automatically.
        </div>
      )}
      {game.status === "failed" && (
        <div className="mb-6 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
          Generation failed{game.status_message ? `: ${game.status_message}` : "."}
        </div>
      )}
      {game.status === "queued" && (
        <div className="mb-6 rounded-lg bg-yellow-500/10 border border-yellow-500/20 px-4 py-3 text-sm text-yellow-400">
          Game is queued for generation. Waiting for worker...
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-800 mb-6">
        <div className="flex gap-6">
          {(["overview", "play", "code", "validate"] as const).map((tab) => (
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

      {/* Overview tab */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {game.status_message && game.status === "ready" && (
            <section>
              <h2 className="text-sm font-medium text-gray-400 mb-2">Summary</h2>
              <p className="text-gray-200">{game.status_message}</p>
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

          {/* Blueprint metadata */}
          {blueprint && (
            <section>
              <h2 className="text-sm font-medium text-gray-400 mb-2">Game Info</h2>
              <div className="grid grid-cols-2 gap-4">
                {blueprint.difficulty && (
                  <div className="rounded-lg bg-gray-900 border border-gray-800 p-3">
                    <p className="text-xs text-gray-500">Difficulty</p>
                    <p className="text-sm font-medium capitalize">{String(blueprint.difficulty)}</p>
                  </div>
                )}
                {blueprint.entrypoint && (
                  <div className="rounded-lg bg-gray-900 border border-gray-800 p-3">
                    <p className="text-xs text-gray-500">Entrypoint</p>
                    <p className="text-sm font-mono">{String(blueprint.entrypoint)}</p>
                  </div>
                )}
                {blueprint.controls && (
                  <div className="rounded-lg bg-gray-900 border border-gray-800 p-3 col-span-2">
                    <p className="text-xs text-gray-500 mb-1">Controls</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(blueprint.controls as Record<string, string>).map(([key, val]) => (
                        <span key={key} className="rounded bg-gray-800 px-2 py-1 text-xs text-gray-300">
                          <span className="text-gray-500">{key}:</span> {val}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Versions */}
          <section>
            <h2 className="text-sm font-medium text-gray-400 mb-2">
              Versions ({versions.length})
            </h2>
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
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium font-mono">v{v.version}</span>
                      {v.blueprint_json && (
                        <span className="text-xs text-gray-500">
                          {String((v.blueprint_json as Record<string, string>)?.difficulty || "")}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Embed snippet */}
          {game.visibility === "public" && game.status === "ready" && (
            <section>
              <h2 className="text-sm font-medium text-gray-400 mb-2">Embed</h2>
              <div className="rounded-lg bg-gray-900 border border-gray-800 p-4">
                <p className="text-xs text-gray-500 mb-2">Copy this HTML to embed this game on your website:</p>
                <code className="block text-xs text-green-400 bg-gray-950 rounded p-3 overflow-x-auto">
                  {`<iframe src="${typeof window !== "undefined" ? window.location.origin : "https://arcadeforge.io"}/embed/games/${gameId}" width="820" height="640" frameborder="0" allow="fullscreen"></iframe>`}
                </code>
              </div>
            </section>
          )}
        </div>
      )}

      {/* Play tab */}
      {activeTab === "play" && (
        <div>
          {game.status !== "ready" ? (
            <div className="rounded-lg bg-gray-900 border border-gray-800 p-8 text-center text-gray-500">
              Game must be in &quot;ready&quot; state to play.
            </div>
          ) : playWsUrl ? (
            <div>
              <GamePlayerNoVNC
                wsUrl={playWsUrl}
                onDisconnect={async () => {
                  if (playSessionId) {
                    await api.games.stopPlay(gameId, playSessionId).catch(() => {});
                  }
                  setPlayWsUrl(null);
                  setPlaySessionId(null);
                }}
              />
              <p className="text-xs text-gray-500 mt-2">
                Session will auto-terminate after {Math.round(settings_sandbox_ttl / 60)} minutes.
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-gray-900 border border-gray-800 p-12 text-center">
              <p className="text-gray-300 text-lg mb-4">Ready to play?</p>
              <button
                onClick={async () => {
                  setPlayLoading(true);
                  try {
                    const result = await api.games.play(gameId);
                    setPlaySessionId(result.session_id);
                    // Poll for session to be ready
                    const pollInterval = setInterval(async () => {
                      try {
                        const session = await api.games.playSession(gameId, result.session_id);
                        if (session.status === "running" && session.ws_url) {
                          clearInterval(pollInterval);
                          setPlayWsUrl(session.ws_url);
                          setPlayLoading(false);
                        } else if (session.status === "failed") {
                          clearInterval(pollInterval);
                          setPlayLoading(false);
                        }
                      } catch {
                        clearInterval(pollInterval);
                        setPlayLoading(false);
                      }
                    }, 2000);
                    // Safety: stop polling after 60s
                    setTimeout(() => {
                      clearInterval(pollInterval);
                      setPlayLoading(false);
                    }, 60000);
                  } catch {
                    setPlayLoading(false);
                  }
                }}
                disabled={playLoading}
                className="rounded-lg bg-green-600 px-8 py-3 font-medium text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {playLoading ? "Starting session..." : "Play Now"}
              </button>
              <p className="text-xs text-gray-500 mt-3">
                Game runs in a secure sandbox container.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Code tab — Monaco Editor */}
      {activeTab === "code" && (
        <div>
          {latestVersion?.source_code ? (
            <GameCodeEditor
              gameId={gameId}
              initialCode={latestVersion.source_code}
              version={latestVersion.version}
              readOnly={!isOwner}
              onSaved={() => loadGame()}
            />
          ) : (
            <div className="rounded-lg bg-gray-900 border border-gray-800 p-8 text-center text-gray-500">
              {game.status === "ready"
                ? "No source code available."
                : "Code will appear here once generation completes."}
            </div>
          )}
        </div>
      )}

      {/* Validate tab */}
      {activeTab === "validate" && (
        <div className="space-y-6">
          {/* Validate button */}
          {isOwner && game.status === "ready" && (
            <button
              onClick={handleValidate}
              disabled={validating}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {validating ? "Validating..." : "Run Validation"}
            </button>
          )}

          {/* Validation runs */}
          {validations.length === 0 ? (
            <div className="rounded-lg bg-gray-900 border border-gray-800 p-8 text-center text-gray-500">
              No validation runs yet.
              {isOwner && " Click 'Run Validation' to scan your game code."}
            </div>
          ) : (
            <div className="space-y-3">
              {validations.map((v) => (
                <div
                  key={v.id}
                  className="rounded-lg bg-gray-900 border border-gray-800 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-xs ${
                          v.status === "passed"
                            ? "bg-green-500/10 text-green-400 border-green-500/20"
                            : v.status === "failed"
                              ? "bg-red-500/10 text-red-400 border-red-500/20"
                              : v.status === "running"
                                ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                        }`}
                      >
                        {v.status}
                      </span>
                      {v.scan_passed !== null && (
                        <span className="text-xs text-gray-500">
                          Code scan: {v.scan_passed ? "passed" : "failed"}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                  {v.report_json_path && (
                    <p className="text-xs text-gray-500 mt-1">{v.report_json_path}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
