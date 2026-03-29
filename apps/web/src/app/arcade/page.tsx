"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, type ArcadeGame } from "@/lib/api";

const GENRES = [
  { id: "", label: "All" },
  { id: "shooter", label: "Shooter" },
  { id: "puzzle", label: "Puzzle" },
  { id: "sports", label: "Sports" },
  { id: "platformer", label: "Platformer" },
];

const SORTS = [
  { id: "trending", label: "Trending" },
  { id: "newest", label: "Newest" },
];

function ArcadeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const q = searchParams.get("q") || "";
  const genre = searchParams.get("genre") || "";
  const sort = searchParams.get("sort") || "trending";

  const [games, setGames] = useState<ArcadeGame[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState(q);

  useEffect(() => {
    setLoading(true);
    api.arcade
      .games({ q, genre, sort, limit: 30 })
      .then((data) => {
        setGames(data.games);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [q, genre, sort]);

  function updateParams(updates: Record<string, string>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(updates)) {
      if (v) params.set(k, v);
      else params.delete(k);
    }
    router.push(`/arcade?${params.toString()}`);
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    updateParams({ q: searchInput });
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Arcade</h1>
        <p className="text-gray-400 mt-1">
          Browse and play AI-generated games.
          {total > 0 && <span className="ml-1">({total} games)</span>}
        </p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <form onSubmit={handleSearch} className="flex-1">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search games..."
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </form>

        {/* Genre filter */}
        <div className="flex gap-2 flex-wrap">
          {GENRES.map((g) => (
            <button
              key={g.id}
              onClick={() => updateParams({ genre: g.id })}
              className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                genre === g.id
                  ? "border-indigo-500 bg-indigo-500/10 text-white"
                  : "border-gray-700 text-gray-400 hover:border-gray-600"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex gap-2">
          {SORTS.map((s) => (
            <button
              key={s.id}
              onClick={() => updateParams({ sort: s.id })}
              className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                sort === s.id
                  ? "border-indigo-500 bg-indigo-500/10 text-white"
                  : "border-gray-700 text-gray-400 hover:border-gray-600"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Game grid */}
      {loading ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
          <p className="text-gray-500">Loading games...</p>
        </div>
      ) : games.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
          <p className="text-gray-500 text-lg mb-2">
            {q || genre ? "No games match your search." : "No public games yet."}
          </p>
          <p className="text-gray-600 text-sm">
            {q || genre ? "Try different search terms or filters." : "Be the first to publish a game!"}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {games.map((game) => (
            <div
              key={game.id}
              className="group rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden hover:border-gray-700 transition-colors"
            >
              {/* Placeholder thumbnail */}
              <Link href={`/games/${game.id}`}>
                <div className="aspect-video bg-gray-800 flex items-center justify-center">
                  <span className="text-4xl text-gray-600">
                    {game.genre === "shooter" ? "🚀" : game.genre === "puzzle" ? "🧩" : game.genre === "sports" ? "🏆" : "🎮"}
                  </span>
                </div>
              </Link>

              <div className="p-4">
                <Link href={`/games/${game.id}`}>
                  <h3 className="font-semibold text-white group-hover:text-indigo-400 transition-colors truncate">
                    {game.title}
                  </h3>
                </Link>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                  <span className="capitalize">{game.genre}</span>
                  <span>·</span>
                  <span>{game.play_count} plays</span>
                  {game.owner_username && (
                    <>
                      <span>·</span>
                      <span>by @{game.owner_username}</span>
                    </>
                  )}
                </div>
                {game.pitch && (
                  <p className="mt-2 text-sm text-gray-400 line-clamp-2">{game.pitch}</p>
                )}
                <div className="flex gap-2 mt-3">
                  <Link
                    href={`/games/${game.id}?tab=play`}
                    className="rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-500 transition-colors"
                  >
                    Play
                  </Link>
                  <Link
                    href={`/games/${game.id}`}
                    className="rounded-lg border border-gray-700 px-4 py-1.5 text-sm text-gray-400 hover:text-gray-300 hover:border-gray-600 transition-colors"
                  >
                    Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

export default function ArcadePage() {
  return (
    <Suspense fallback={<div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center"><p className="text-gray-400">Loading arcade...</p></div>}>
      <ArcadeContent />
    </Suspense>
  );
}
