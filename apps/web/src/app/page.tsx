import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center px-4">
      <h1 className="text-5xl font-bold tracking-tight">ArcadeForge</h1>
      <p className="mt-4 text-lg text-gray-400">
        Generate. Play. Share. AI-powered browser arcade.
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          href="/auth/register"
          className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          Get Started
        </Link>
        <Link
          href="/arcade"
          className="rounded-lg border border-gray-700 px-6 py-3 font-medium text-gray-300 hover:border-gray-500 transition-colors"
        >
          Browse Games
        </Link>
      </div>
    </main>
  );
}
