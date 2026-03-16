import Link from "next/link";

const FEATURES = [
  {
    title: "AI Game Generation",
    description: "Describe your game idea, pick a genre, and AI generates playable Pygame code in seconds.",
    icon: "sparkles",
  },
  {
    title: "Play in Browser",
    description: "No downloads, no installs. Games run in secure sandbox containers with full keyboard and mouse support.",
    icon: "play",
  },
  {
    title: "Edit with Monaco",
    description: "Full code editor with syntax highlighting. Edit, save new versions, and auto-validate your changes.",
    icon: "code",
  },
  {
    title: "Share & Embed",
    description: "Share games with a link, embed them on any website, or fork public games to remix them.",
    icon: "share",
  },
];

const GENRES = [
  { name: "Space Shooter", emoji: "rocket" },
  { name: "Puzzle", emoji: "puzzle" },
  { name: "Sports / Pong", emoji: "trophy" },
  { name: "Platformer", emoji: "gamepad" },
];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-4 py-24 text-center">
        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight max-w-3xl">
          Generate. Play. Share.
          <span className="block text-indigo-400 mt-2">AI-Powered Browser Arcade.</span>
        </h1>
        <p className="mt-6 text-lg text-gray-400 max-w-2xl">
          ArcadeForge lets you create games with AI, play them instantly in your browser,
          edit the code, and share with the world. No downloads. No installs.
        </p>
        <div className="mt-10 flex gap-4">
          <Link
            href="/auth/register"
            className="rounded-lg bg-indigo-600 px-8 py-3.5 font-medium text-white hover:bg-indigo-500 transition-colors text-lg"
          >
            Get Started Free
          </Link>
          <Link
            href="/arcade"
            className="rounded-lg border border-gray-700 px-8 py-3.5 font-medium text-gray-300 hover:border-gray-500 transition-colors text-lg"
          >
            Browse Games
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 text-xl">
                {f.icon === "sparkles" ? "AI" : f.icon === "play" ? ">" : f.icon === "code" ? "</>" : "->"}
              </div>
              <h3 className="font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-gray-400">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Genres */}
      <section className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Pick a Genre, Start Creating</h2>
        <p className="text-gray-400 mb-8">
          Choose from our expanding library of game genres. Each genre comes with
          optimized templates and difficulty presets.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          {GENRES.map((g) => (
            <div
              key={g.name}
              className="rounded-xl border border-gray-800 bg-gray-900/50 px-6 py-4 text-center min-w-[140px]"
            >
              <p className="text-2xl mb-1">{g.emoji === "rocket" ? "🚀" : g.emoji === "puzzle" ? "🧩" : g.emoji === "trophy" ? "🏆" : "🎮"}</p>
              <p className="text-sm font-medium text-gray-300">{g.name}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-20 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to Build?</h2>
        <p className="text-gray-400 mb-8 max-w-lg mx-auto">
          Join ArcadeForge and start creating AI-generated games today.
          Free to use. Open source.
        </p>
        <Link
          href="/auth/register"
          className="rounded-lg bg-indigo-600 px-8 py-3.5 font-medium text-white hover:bg-indigo-500 transition-colors text-lg"
        >
          Create Your First Game
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 px-4 py-8">
        <div className="mx-auto max-w-6xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            ArcadeForge — Open Source AI Game Platform
          </p>
          <div className="flex gap-6 text-sm text-gray-500">
            <a href="https://github.com/michelbr84/arcadeforge" target="_blank" rel="noopener noreferrer" className="hover:text-gray-300 transition-colors">
              GitHub
            </a>
            <Link href="/arcade" className="hover:text-gray-300 transition-colors">
              Arcade
            </Link>
            <a href="/api/docs" className="hover:text-gray-300 transition-colors">
              API Docs
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
