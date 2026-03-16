import type { Metadata } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Props = {
  params: Promise<{ gameId: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { gameId } = await params;

  try {
    const res = await fetch(`${API_BASE}/api/games/${gameId}`, {
      next: { revalidate: 60 },
    });

    if (!res.ok) {
      return { title: "Game — ArcadeForge" };
    }

    const game = await res.json();

    return {
      title: `${game.title} — ArcadeForge`,
      description: game.pitch || `A ${game.genre} game on ArcadeForge`,
      openGraph: {
        title: game.title,
        description: game.pitch || `A ${game.genre} game on ArcadeForge`,
        type: "website",
        url: `https://arcadeforge.io/games/${gameId}`,
        siteName: "ArcadeForge",
      },
      twitter: {
        card: "summary_large_image",
        title: game.title,
        description: game.pitch || `A ${game.genre} game on ArcadeForge`,
      },
    };
  } catch {
    return { title: "Game — ArcadeForge" };
  }
}

export default function GameLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
