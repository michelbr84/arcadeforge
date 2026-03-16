"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuthStore();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Welcome back, @{user.username}
          </p>
        </div>
        <a
          href="/create"
          className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          Create Game
        </a>
      </div>

      {/* My Games — placeholder grid */}
      <section>
        <h2 className="text-lg font-semibold mb-4">My Games</h2>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
          <p className="text-gray-500 text-lg mb-2">No games yet</p>
          <p className="text-gray-600 text-sm">
            Create your first AI-generated game to get started.
          </p>
        </div>
      </section>

      {/* Recent Validations — placeholder */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold mb-4">Recent Validations</h2>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-8 text-center">
          <p className="text-gray-500">No validation runs yet.</p>
        </div>
      </section>
    </main>
  );
}
