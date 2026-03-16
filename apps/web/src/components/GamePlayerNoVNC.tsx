"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  wsUrl: string;
  onDisconnect?: () => void;
};

/**
 * Embeds a noVNC session in an iframe.
 *
 * The sandbox container runs websockify which serves noVNC static files
 * at the root and proxies VNC over WebSocket. We point an iframe at
 * the noVNC HTML page with auto-connect parameters.
 */
export default function GamePlayerNoVNC({ wsUrl, onDisconnect }: Props) {
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  // Convert ws:// URL to http:// for the noVNC HTML page
  // ws://localhost:6100 → http://localhost:6100/vnc.html?autoconnect=true&resize=scale
  const httpUrl = wsUrl.replace("ws://", "http://").replace("wss://", "https://");
  const novncUrl = `${httpUrl}/vnc.html?autoconnect=true&resize=scale&reconnect=true&reconnect_delay=1000`;

  useEffect(() => {
    // Simple timer to mark as "connected" after iframe loads
    const timer = setTimeout(() => setStatus("connected"), 3000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="rounded-lg border border-gray-800 overflow-hidden bg-black">
      {/* Status bar */}
      <div className="flex items-center justify-between bg-gray-900 px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              status === "connected"
                ? "bg-green-400"
                : status === "connecting"
                  ? "bg-yellow-400 animate-pulse"
                  : "bg-red-400"
            }`}
          />
          <span className="text-xs text-gray-400 capitalize">{status}</span>
        </div>
        {onDisconnect && (
          <button
            onClick={onDisconnect}
            className="text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Stop Session
          </button>
        )}
      </div>

      {/* noVNC iframe */}
      <iframe
        src={novncUrl}
        className="w-full aspect-[4/3] bg-black"
        style={{ minHeight: "480px" }}
        allow="fullscreen"
        sandbox="allow-scripts allow-same-origin"
      />
    </div>
  );
}
