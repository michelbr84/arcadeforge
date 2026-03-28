#!/bin/bash
# ArcadeForge Sandbox Entrypoint
# Starts: Xvfb → x11vnc → websockify/noVNC → game
#
# Game loading modes (in priority order):
#   1. GAME_DOWNLOAD_URL — download & extract a game archive from S3/MinIO
#   2. GAME_WORKSPACE_PATH — use a local path (for dev/volume mounts)
#   3. Volume mount at /game (original default)
set -e

# ---- Download game files if GAME_DOWNLOAD_URL is set ----
if [ -n "${GAME_DOWNLOAD_URL}" ]; then
    echo "[sandbox] Downloading game from presigned URL..."
    DOWNLOAD_DIR="/tmp/game_download"
    mkdir -p "${DOWNLOAD_DIR}" /game 2>/dev/null || true

    # Download the archive/file
    wget -q -O "${DOWNLOAD_DIR}/game_archive" "${GAME_DOWNLOAD_URL}" || {
        echo "[sandbox] ERROR: Failed to download game from URL"
        exit 1
    }

    # Detect file type and extract accordingly
    FILE_TYPE=$(file -b --mime-type "${DOWNLOAD_DIR}/game_archive" 2>/dev/null || echo "unknown")
    echo "[sandbox] Downloaded file type: ${FILE_TYPE}"

    case "${FILE_TYPE}" in
        application/zip)
            unzip -q -o "${DOWNLOAD_DIR}/game_archive" -d /game/ 2>/dev/null || {
                echo "[sandbox] ERROR: Failed to unzip game archive"
                exit 1
            }
            ;;
        application/gzip|application/x-gzip|application/x-tar)
            tar xzf "${DOWNLOAD_DIR}/game_archive" -C /game/ 2>/dev/null || \
            tar xf "${DOWNLOAD_DIR}/game_archive" -C /game/ 2>/dev/null || {
                echo "[sandbox] ERROR: Failed to extract game archive"
                exit 1
            }
            ;;
        text/x-python|text/plain)
            # Single Python file — just copy it
            cp "${DOWNLOAD_DIR}/game_archive" /game/main.py
            ;;
        *)
            # Try as zip first, then tar, then treat as single file
            unzip -q -o "${DOWNLOAD_DIR}/game_archive" -d /game/ 2>/dev/null || \
            tar xzf "${DOWNLOAD_DIR}/game_archive" -C /game/ 2>/dev/null || \
            cp "${DOWNLOAD_DIR}/game_archive" /game/main.py
            ;;
    esac

    rm -rf "${DOWNLOAD_DIR}"
    echo "[sandbox] Game files extracted to /game/"
    ls -la /game/
elif [ -n "${GAME_WORKSPACE_PATH}" ] && [ -d "${GAME_WORKSPACE_PATH}" ]; then
    echo "[sandbox] Using game workspace from path: ${GAME_WORKSPACE_PATH}"
    # Copy files to /game if they are not already there
    if [ "${GAME_WORKSPACE_PATH}" != "/game" ]; then
        cp -r "${GAME_WORKSPACE_PATH}"/* /game/ 2>/dev/null || true
    fi
fi

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
