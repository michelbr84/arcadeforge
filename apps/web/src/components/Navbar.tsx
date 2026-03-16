"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

export default function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  return (
    <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-lg font-bold text-white">
              ArcadeForge
            </Link>
            {user && (
              <>
                <Link
                  href="/dashboard"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/arcade"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Arcade
                </Link>
              </>
            )}
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Link
                  href="/dashboard"
                  className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
                >
                  Create Game
                </Link>
                <Link
                  href={`/u/${user.username}`}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  @{user.username}
                </Link>
                <Link
                  href="/settings"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  href="/auth/register"
                  className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
