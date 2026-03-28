"""Sandbox container orchestrator.

Manages the lifecycle of game play session containers:
- Start: launch container with game code mounted
- Status: check if container is running
- Stop: kill container and clean up
- Reap: clean up expired containers by TTL

Supports two drivers selected via ``settings.sandbox_driver``:
- ``"docker"`` (default): local Docker containers
- ``"fly"``: Fly.io Machines for cloud deployments

Each container runs: Xvfb + x11vnc + websockify + game
and exposes a WebSocket endpoint for noVNC connection.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import docker
from docker.errors import NotFound as DockerNotFound

from app.config import settings

logger = logging.getLogger("arcadeforge.sandbox")

# Base port for websockify — each session gets a unique port
_BASE_WS_PORT = 6100
_MAX_CONCURRENT = 50


# ---------------------------------------------------------------------------
# Driver dispatcher
# ---------------------------------------------------------------------------

async def start_sandbox_dispatch(
    session_id: str,
    game_workspace_path: str,
    port: int,
) -> dict[str, Any]:
    """Start a sandbox using the configured driver.

    This is the primary entry point for new code. It delegates to either
    the local Docker driver or the Fly.io Machines driver based on
    ``settings.sandbox_driver``.

    Args:
        session_id: Unique play session ID.
        game_workspace_path: Path (or S3 key) to the game workspace.
        port: Host port for websockify (used only by the Docker driver).

    Returns:
        dict with connection details (keys vary by driver).
    """
    if settings.sandbox_driver == "fly":
        from app.games.sandbox_fly import create_machine

        result = await create_machine(session_id, game_workspace_path)
        # Normalize return keys so the worker can use a consistent interface
        return {
            "container_id": result["machine_id"],
            "container_name": result["machine_id"],
            "ws_url": result["ws_url"],
            "ws_port": 6080,
            "status": "running",
            "public_url": result.get("public_url", ""),
        }
    else:
        # Docker driver — synchronous, run in thread
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            start_sandbox,
            session_id,
            game_workspace_path,
            port,
        )


async def stop_sandbox_dispatch(sandbox_ref: str) -> bool:
    """Stop a sandbox using the configured driver.

    Args:
        sandbox_ref: Container name (Docker) or machine ID (Fly).

    Returns:
        True if stopped successfully.
    """
    if settings.sandbox_driver == "fly":
        from app.games.sandbox_fly import destroy_machine

        return await destroy_machine(sandbox_ref)
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, stop_sandbox, sandbox_ref)


async def get_sandbox_status_dispatch(sandbox_ref: str) -> str:
    """Get sandbox status using the configured driver."""
    if settings.sandbox_driver == "fly":
        from app.games.sandbox_fly import get_machine_status

        return await get_machine_status(sandbox_ref)
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_sandbox_status, sandbox_ref)


# ---------------------------------------------------------------------------
# Docker driver (original implementation)
# ---------------------------------------------------------------------------


def _get_docker_client():
    """Get Docker client. Uses default socket."""
    return docker.from_env()


def start_sandbox(
    session_id: str,
    game_workspace_path: str,
    port: int,
) -> dict:
    """Start a sandbox container for a play session.

    Args:
        session_id: Unique play session ID
        game_workspace_path: Path to the game's workspace directory
        port: Host port for websockify WebSocket

    Returns:
        dict with container_id, ws_url, status
    """
    client = _get_docker_client()
    container_name = f"af-play-{session_id[:12]}"

    # Normalize path for Docker Desktop on Windows
    # Docker Desktop accepts forward-slash paths like G:/Projetos/...
    game_workspace_path = game_workspace_path.replace("\\", "/")

    sandbox_image = settings.sandbox_image_name
    ttl = settings.sandbox_session_ttl_seconds
    cpu_limit = settings.sandbox_cpu_limit
    mem_limit = f"{settings.sandbox_mem_limit_mb}m"

    logger.info(f"Starting sandbox {container_name} on port {port}")

    try:
        container = client.containers.run(
            image=sandbox_image,
            name=container_name,
            detach=True,
            # Mount game files read-only
            volumes={
                game_workspace_path: {"bind": "/game", "mode": "ro"},
            },
            # Environment
            environment={
                "GAME_FILE": "/game/main.py",
                "SCREEN_WIDTH": "800",
                "SCREEN_HEIGHT": "600",
            },
            # Port: expose websockify
            ports={"6080/tcp": port},
            # Resource limits
            cpu_period=100000,
            cpu_quota=int(cpu_limit * 100000),
            mem_limit=mem_limit,
            # Security — network_mode="none" blocks port publishing,
            # so in dev we must use "bridge". In production, use a WebSocket
            # proxy that routes to the container's internal network.
            network_mode="bridge",
            read_only=True,
            tmpfs={"/tmp": "size=100M,mode=1777"},
            # Auto-remove on stop
            auto_remove=True,
            # Stop after TTL
            stop_signal="SIGTERM",
            labels={
                "arcadeforge.session": session_id,
                "arcadeforge.type": "sandbox",
            },
        )

        ws_url = f"ws://localhost:{port}"

        logger.info(f"Sandbox {container_name} started: {container.short_id}")

        return {
            "container_id": container.id,
            "container_name": container_name,
            "ws_url": ws_url,
            "ws_port": port,
            "status": "running",
        }

    except Exception as e:
        logger.exception(f"Failed to start sandbox {container_name}")
        raise


def stop_sandbox(container_name: str) -> bool:
    """Stop and remove a sandbox container."""
    client = _get_docker_client()
    try:
        container = client.containers.get(container_name)
        container.stop(timeout=5)
        logger.info(f"Sandbox {container_name} stopped")
        return True
    except DockerNotFound:
        logger.warning(f"Sandbox {container_name} not found (already stopped?)")
        return False
    except Exception as e:
        logger.exception(f"Failed to stop sandbox {container_name}")
        return False


def get_sandbox_status(container_name: str) -> str:
    """Check if a sandbox container is running."""
    client = _get_docker_client()
    try:
        container = client.containers.get(container_name)
        return container.status  # "running", "exited", etc.
    except DockerNotFound:
        return "stopped"
    except Exception:
        return "unknown"


def allocate_port(existing_ports: set[int]) -> int:
    """Allocate a free port for a new sandbox session.

    Scans from _BASE_WS_PORT upward, skipping ports already in use.
    """
    for port in range(_BASE_WS_PORT, _BASE_WS_PORT + _MAX_CONCURRENT):
        if port not in existing_ports:
            return port
    raise RuntimeError("No free ports for sandbox sessions")
