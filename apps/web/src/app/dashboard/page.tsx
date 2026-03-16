"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";
import { api, type Game, type GameStatus } from "@/lib/api";

const STATUS_STYLES: Record<GameStatus, string> = {
  queued: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  generating: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  ready: "bg-green-500/10 text-green-400 border-green-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuthStore();
  const [games, setGames] = useState<Game[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user) return;
    api.games
      .list(50, 0)
      .then((data) => {
        setGames(data.games);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (authLoading || !user) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Welcome back, @{user.username}
            {total > 0 && <span className="ml-2 text-gray-500">({total} games)</span>}
          </p>
        </div>
        <Link
          href="/create"
          className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          Create Game
        </Link>
      </div>

      {/* Games list */}
      <section>
        <h2 className="text-lg font-semibold mb-4">My Games</h2>
        {loading ? (
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-8 text-center">
            <p className="text-gray-500">Loading games...</p>
          </div>
        ) : games.length === 0 ? (
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
            <p className="text-gray-500 text-lg mb-2">No games yet</p>
            <p className="text-gray-600 text-sm mb-4">
              Create your first AI-generated game to get started.
            </p>
            <Link
              href="/create"
              className="inline-block rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              Create Game
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {games.map((game) => (
              <Link
                key={game.id}
                href={`/games/${game.id}`}
                className="group rounded-xl border border-gray-800 bg-gray-900/50 p-5 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-white group-hover:text-indigo-400 transition-colors truncate pr-2">
                    {game.title}
                  </h3>
                  <span
                    className={`shrink-0 rounded-full border px-2 py-0.5 text-xs capitalize ${
                      STATUS_STYLES[game.status] || STATUS_STYLES.queued
                    }`}
                  >
                    {game.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="capitalize">{game.genre}</span>
                  <span>·</span>
                  <span>{game.play_count} plays</span>
                  <span>·</span>
                  <span>{new Date(game.created_at).toLocaleDateString()}</span>
                </div>
                {game.pitch && (
                  <p className="mt-2 text-sm text-gray-400 line-clamp-2">{game.pitch}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
