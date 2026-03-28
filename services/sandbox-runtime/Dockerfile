# ArcadeForge Sandbox Runtime
# Runs Pygame games in a virtual display with VNC + noVNC (websockify)
#
# Security: runs as non-root, no network in production, read-only FS except /tmp
# Build: docker build -t arcadeforge-sandbox:latest services/sandbox-runtime/

FROM python:3.12-slim-bookworm

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install X11, VNC, websockify, and audio stubs
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    python3-pygame \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    fonts-dejavu-core \
    procps \
    wget \
    file \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install pygame via pip as well (for latest version)
RUN pip install --no-cache-dir pygame-ce 2>/dev/null || pip install --no-cache-dir pygame

# Create non-root user for sandbox
RUN groupadd -r sandbox && useradd -r -g sandbox -m -d /home/sandbox sandbox

# Create required directories
RUN mkdir -p /game /tmp/.X11-unix && \
    chown sandbox:sandbox /game /tmp/.X11-unix

# noVNC static files location (Debian package installs to /usr/share/novnc)
ENV NOVNC_PATH=/usr/share/novnc

# Display configuration
ENV DISPLAY=:99
ENV SDL_VIDEODRIVER=x11
ENV SDL_AUDIODRIVER=dummy
ENV PYTHONUNBUFFERED=1

# Game resolution
ENV SCREEN_WIDTH=800
ENV SCREEN_HEIGHT=600
ENV SCREEN_DEPTH=24

# VNC port (internal)
ENV VNC_PORT=5900
# WebSocket port (exposed)
ENV WS_PORT=6080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER sandbox
WORKDIR /game

EXPOSE 6080

ENTRYPOINT ["/entrypoint.sh"]
