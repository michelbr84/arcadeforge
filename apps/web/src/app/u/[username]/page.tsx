"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type User, ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

export default function UserProfilePage() {
  const params = useParams();
  const username = params.username as string;
  const currentUser = useAuthStore((s) => s.user);

  const [profile, setProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isOwnProfile = currentUser?.username === username?.toLowerCase();

  useEffect(() => {
    if (!username) return;

    setLoading(true);
    setError(null);
    api.users
      .getProfile(username)
      .then(setProfile)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setError("User not found.");
        } else {
          setError("Failed to load profile.");
        }
      })
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </main>
    );
  }

  if (error || !profile) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center">
        <h1 className="text-2xl font-bold text-gray-400 mb-2">
          {error || "User not found"}
        </h1>
        <Link href="/" className="text-indigo-400 hover:text-indigo-300 text-sm">
          Go home
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Profile header */}
      <div className="flex items-center gap-6 mb-8">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-indigo-600 text-2xl font-bold">
          {profile.username[0].toUpperCase()}
        </div>
        <div>
          <h1 className="text-2xl font-bold">@{profile.username}</h1>
          <p className="text-sm text-gray-400">
            Joined {new Date(profile.created_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
            })}
          </p>
          {isOwnProfile && (
            <Link
              href="/settings"
              className="mt-1 inline-block text-sm text-indigo-400 hover:text-indigo-300"
            >
              Edit profile
            </Link>
          )}
        </div>
      </div>

      {/* Games section — placeholder */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Games</h2>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
          <p className="text-gray-500 text-lg mb-2">No published games yet</p>
          {isOwnProfile && (
            <Link
              href="/dashboard"
              className="text-sm text-indigo-400 hover:text-indigo-300"
            >
              Create your first game
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}
