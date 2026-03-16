"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { api, type Genre, ApiError } from "@/lib/api";

export default function CreateGamePage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuthStore();

  const [genres, setGenres] = useState<Genre[]>([]);
  const [genre, setGenre] = useState("");
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login");
    }
  }, [user, authLoading, router]);

  // Load genres
  useEffect(() => {
    api.games.genres().then((data) => {
      setGenres(data);
      if (data.length > 0) setGenre(data[0].id);
    });
  }, []);

  const selectedGenre = genres.find((g) => g.id === genre);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const result = await api.games.create({ genre, title, prompt, difficulty });
      router.push(`/games/${result.game_id}`);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to create game.";
      setError(message);
      setSubmitting(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-2xl font-bold mb-2">Create a Game</h1>
      <p className="text-gray-400 mb-8">
        Choose a genre, describe your game, and AI will generate it for you.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Genre selector */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Genre
          </label>
          <div className="grid grid-cols-2 gap-3">
            {genres.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => { setGenre(g.id); setDifficulty("medium"); }}
                className={`rounded-xl border p-4 text-left transition-colors ${
                  genre === g.id
                    ? "border-indigo-500 bg-indigo-500/10"
                    : "border-gray-700 bg-gray-900 hover:border-gray-600"
                }`}
              >
                <p className="font-medium text-white">{g.name}</p>
                <p className="text-xs text-gray-400 mt-1">{g.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-1">
            Title
          </label>
          <input
            id="title"
            type="text"
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="My Awesome Space Shooter"
          />
        </div>

        {/* Prompt */}
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-300 mb-1">
            Describe your game
          </label>
          <textarea
            id="prompt"
            required
            minLength={10}
            maxLength={2000}
            rows={5}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
            placeholder="Create a space shooter with asteroids, power-ups, and a score system. The player controls a spaceship that can shoot lasers..."
          />
          <p className="mt-1 text-xs text-gray-500">
            {prompt.length}/2000 characters
          </p>
        </div>

        {/* Difficulty */}
        {selectedGenre && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Difficulty
            </label>
            <div className="flex gap-3">
              {selectedGenre.difficulty_options.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDifficulty(d)}
                  className={`rounded-lg border px-4 py-2 text-sm capitalize transition-colors ${
                    difficulty === d
                      ? "border-indigo-500 bg-indigo-500/10 text-white"
                      : "border-gray-700 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !genre || !title || prompt.length < 10}
          className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Creating game..." : "Generate Game"}
        </button>
      </form>
    </main>
  );
}
