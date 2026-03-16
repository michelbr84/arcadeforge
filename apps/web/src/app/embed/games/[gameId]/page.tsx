"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, type Game, ApiError } from "@/lib/api";
import GamePlayerNoVNC from "@/components/GamePlayerNoVNC";

/**
 * Embeddable game player — minimal chrome, designed for iframe embedding.
 * URL: /embed/games/[gameId]
 *
 * This page has no navbar, no sidebar, just the game player.
 * Intended to be embedded via:
 *   <iframe src="https://arcadeforge.io/embed/games/[id]" />
 */
export default function EmbedGamePage() {
  const params = useParams();
  const gameId = params.gameId as string;

  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playSessionId, setPlaySessionId] = useState<string | null>(null);
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    api.games
      .get(gameId)
      .then(setGame)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Game not found."))
      .finally(() => setLoading(false));
  }, [gameId]);

  const startPlay = useCallback(async () => {
    if (!gameId || starting) return;
    setStarting(true);
    try {
      const result = await api.games.play(gameId);
      setPlaySessionId(result.session_id);

      // Poll for session ready
      const poll = setInterval(async () => {
        try {
          const session = await api.games.playSession(gameId, result.session_id);
          if (session.status === "running" && session.ws_url) {
            clearInterval(poll);
            setWsUrl(session.ws_url);
            setStarting(false);
          } else if (session.status === "failed") {
            clearInterval(poll);
            setError("Failed to start game.");
            setStarting(false);
          }
        } catch {
          clearInterval(poll);
          setStarting(false);
        }
      }, 2000);

      setTimeout(() => { clearInterval(poll); setStarting(false); }, 60000);
    } catch {
      setError("Failed to start play session.");
      setStarting(false);
    }
  }, [gameId, starting]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black text-white">
        <p>Loading...</p>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="flex h-screen items-center justify-center bg-black text-white">
        <p>{error || "Game not found."}</p>
      </div>
    );
  }

  if (wsUrl) {
    return (
      <div className="h-screen bg-black">
        <GamePlayerNoVNC
          wsUrl={wsUrl}
          onDisconnect={async () => {
            if (playSessionId) {
              await api.games.stopPlay(gameId, playSessionId).catch(() => {});
            }
            setWsUrl(null);
            setPlaySessionId(null);
          }}
        />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-black text-white">
      <h2 className="text-xl font-bold mb-2">{game.title}</h2>
      <p className="text-gray-400 text-sm mb-4 capitalize">{game.genre}</p>
      <button
        onClick={startPlay}
        disabled={starting || game.status !== "ready"}
        className="rounded-lg bg-green-600 px-8 py-3 font-medium text-white hover:bg-green-500 disabled:opacity-50 transition-colors"
      >
        {starting ? "Starting..." : "Play"}
      </button>
      <p className="text-xs text-gray-600 mt-4">
        Powered by <a href="https://arcadeforge.io" target="_blank" rel="noopener noreferrer" className="text-indigo-400">ArcadeForge</a>
      </p>
    </div>
  );
}
