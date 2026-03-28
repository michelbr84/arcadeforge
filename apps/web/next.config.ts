import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Proxy all /api/* requests to the FastAPI backend.
        // This keeps cookies on the same origin, avoiding CORS issues.
        // API_URL is server-side only (NOT NEXT_PUBLIC_) — set it on Vercel
        // to point to the Railway/production backend URL.
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
