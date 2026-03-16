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
sleep 2
echo "[sandbox] Xvfb started (PID: $XVFB_PID)"

# Start x11vnc (VNC server — listen on all interfaces so websockify can connect)
x11vnc -display ${DISPLAY} \
    -nopw \
    -rfbport ${VNC_PORT} \
    -shared \
    -forever \
    -noxdamage \
    -quiet &
X11VNC_PID=$!

sleep 1
echo "[sandbox] x11vnc started (PID: $X11VNC_PID)"

# Start websockify (WebSocket → TCP bridge for noVNC)
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
    # Keep services alive so the user sees something in noVNC
    sleep 30
    exit 1
fi

echo "[sandbox] Starting game: $GAME_FILE"
python3 "$GAME_FILE" &
GAME_PID=$!

echo "[sandbox] Game started (PID: $GAME_PID)"
echo "[sandbox] noVNC available at http://localhost:${WS_PORT}/vnc.html"

# Wait for game to finish
wait $GAME_PID 2>/dev/null
EXIT_CODE=$?
echo "[sandbox] Game exited with code $EXIT_CODE"

# Keep VNC/websockify alive for 30s after game exits
# so the user can see the final state or error
echo "[sandbox] Keeping display alive for 30s..."
sleep 30

# Cleanup
kill $WS_PID $X11VNC_PID $XVFB_PID 2>/dev/null
exit $EXIT_CODE
