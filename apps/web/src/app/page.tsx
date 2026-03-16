export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-950 text-white">
      <h1 className="text-5xl font-bold tracking-tight">ArcadeForge</h1>
      <p className="mt-4 text-lg text-gray-400">
        Generate. Play. Share. AI-powered browser arcade.
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/auth/register"
          className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          Get Started
        </a>
        <a
          href="/arcade"
          className="rounded-lg border border-gray-700 px-6 py-3 font-medium text-gray-300 hover:border-gray-500 transition-colors"
        >
          Browse Games
        </a>
      </div>
    </main>
  );
}
