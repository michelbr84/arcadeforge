#!/bin/bash
# ArcadeForge Sandbox Entrypoint
# Starts: Xvfb → x11vnc → websockify/noVNC → game
set -e

echo "[sandbox] Starting virtual display ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"

# Start Xvfb (virtual framebuffer)
Xvfb ${DISPLAY} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} \
    -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to be ready
sleep 1
echo "[sandbox] Xvfb started (PID: $XVFB_PID)"

# Start x11vnc (VNC server, no password for internal use, listen on localhost only)
x11vnc -display ${DISPLAY} \
    -nopw \
    -listen localhost \
    -rfbport ${VNC_PORT} \
    -shared \
    -forever \
    -noxdamage \
    -quiet &
X11VNC_PID=$!

sleep 1
echo "[sandbox] x11vnc started (PID: $X11VNC_PID)"

# Start websockify (WebSocket → TCP bridge for noVNC)
# Serves noVNC static files AND proxies WebSocket to VNC
websockify --web=${NOVNC_PATH} \
    ${WS_PORT} \
    localhost:${VNC_PORT} &
WS_PID=$!

sleep 1
echo "[sandbox] websockify started on port ${WS_PORT} (PID: $WS_PID)"

# Run the game
GAME_FILE="${GAME_FILE:-/game/main.py}"
if [ ! -f "$GAME_FILE" ]; then
    echo "[sandbox] ERROR: Game file not found: $GAME_FILE"
    exit 1
fi

echo "[sandbox] Starting game: $GAME_FILE"
python3 "$GAME_FILE" &
GAME_PID=$!

echo "[sandbox] Game started (PID: $GAME_PID)"
echo "[sandbox] noVNC available at http://localhost:${WS_PORT}/vnc.html"

# Wait for game to finish (or be killed by TTL)
wait $GAME_PID 2>/dev/null
EXIT_CODE=$?

echo "[sandbox] Game exited with code $EXIT_CODE"

# Cleanup
kill $WS_PID $X11VNC_PID $XVFB_PID 2>/dev/null
exit $EXIT_CODE
