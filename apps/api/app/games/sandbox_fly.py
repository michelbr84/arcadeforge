"""Fly.io Machines sandbox driver for cloud deployments.

Alternative to the Docker-based sandbox (sandbox.py) for running game
sandboxes on Fly.io Machines instead of local Docker containers.

Each machine runs the same sandbox image (Xvfb + VNC + noVNC + game)
and is automatically destroyed when done.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("arcadeforge.sandbox_fly")

FLY_API_BASE = "https://api.machines.dev/v1"


def _fly_headers() -> dict[str, str]:
    """Build authorization headers for Fly.io Machines API."""
    return {
        "Authorization": f"Bearer {settings.fly_api_token}",
        "Content-Type": "application/json",
    }


async def create_machine(
    session_id: str,
    game_s3_key: str,
    *,
    ttl_seconds: int = 300,
) -> dict[str, Any]:
    """Create a Fly Machine to run a game sandbox.

    Args:
        session_id: Unique play session ID.
        game_s3_key: S3/MinIO key (or local path) for the game workspace.
            When storage_driver is "local", a presigned URL is not available,
            so the path is passed directly as GAME_WORKSPACE_PATH.
        ttl_seconds: Time-to-live for the machine in seconds.

    Returns:
        dict with:
        - machine_id: str
        - ws_url: str (WebSocket URL for noVNC)
        - public_url: str
    """
    headers = _fly_headers()
    app_name = settings.fly_sandbox_app

    # Build environment for the sandbox container
    env: dict[str, str] = {
        "SESSION_ID": session_id,
        "SCREEN_WIDTH": "800",
        "SCREEN_HEIGHT": "600",
    }

    # If we have S3/MinIO storage, generate a presigned download URL
    # so the sandbox can fetch the game files on startup.
    if settings.storage_driver != "local":
        from app.storage import get_presigned_url

        game_url = await get_presigned_url(game_s3_key)
        env["GAME_DOWNLOAD_URL"] = game_url
    else:
        # Local storage — pass the path directly (useful for dev with
        # Fly Machines running on the same host, e.g. via flyctl local)
        env["GAME_WORKSPACE_PATH"] = game_s3_key

    machine_config = {
        "name": f"sandbox-{session_id[:12]}",
        "config": {
            "image": f"registry.fly.io/{app_name}:latest",
            "env": env,
            "services": [
                {
                    "ports": [{"port": 6080, "handlers": ["http"]}],
                    "protocol": "tcp",
                    "internal_port": 6080,
                }
            ],
            "auto_destroy": True,
            "restart": {"policy": "no"},
            "guest": {
                "cpu_kind": "shared",
                "cpus": 1,
                "memory_mb": settings.sandbox_mem_limit_mb
                if settings.sandbox_mem_limit_mb <= 1024
                else 1024,
            },
            "metadata": {
                "arcadeforge_session": session_id,
                "arcadeforge_type": "sandbox",
            },
        },
        "region": settings.fly_sandbox_region,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FLY_API_BASE}/apps/{app_name}/machines",
            json=machine_config,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

    machine_id = data["id"]

    # Wait for the machine to be started before returning
    await _wait_for_state(machine_id, "started")

    public_url = f"https://{machine_id}.fly.dev"
    ws_url = f"wss://{machine_id}.fly.dev/websockify"

    logger.info(
        f"Fly machine {machine_id} created for session {session_id}: {public_url}"
    )

    return {
        "machine_id": machine_id,
        "ws_url": ws_url,
        "public_url": public_url,
    }


async def destroy_machine(machine_id: str) -> bool:
    """Stop and destroy a Fly Machine.

    Args:
        machine_id: The Fly Machine ID to destroy.

    Returns:
        True if the machine was successfully stopped/destroyed, False otherwise.
    """
    headers = _fly_headers()
    app_name = settings.fly_sandbox_app

    async with httpx.AsyncClient() as client:
        # First, send a stop signal
        try:
            resp = await client.post(
                f"{FLY_API_BASE}/apps/{app_name}/machines/{machine_id}/stop",
                headers=headers,
                timeout=15,
            )
            # 200 = stopped, 404 = already gone — both are fine
            if resp.status_code == 404:
                logger.info(f"Fly machine {machine_id} already gone")
                return True
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.info(f"Fly machine {machine_id} not found (already destroyed)")
                return True
            logger.exception(f"Failed to stop Fly machine {machine_id}")
            return False

        # Wait for stopped state, then destroy
        try:
            await _wait_for_state(machine_id, "stopped", timeout=30)
        except TimeoutError:
            logger.warning(
                f"Fly machine {machine_id} did not reach stopped state, "
                f"proceeding with destroy"
            )

        # Destroy the machine
        try:
            resp = await client.delete(
                f"{FLY_API_BASE}/apps/{app_name}/machines/{machine_id}",
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 404:
                return True
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return True
            logger.exception(f"Failed to destroy Fly machine {machine_id}")
            return False

    logger.info(f"Fly machine {machine_id} destroyed")
    return True


async def get_machine_status(machine_id: str) -> str:
    """Get the current state of a Fly Machine.

    Returns one of: "created", "starting", "started", "stopping",
    "stopped", "destroying", "destroyed", or "unknown".
    """
    headers = _fly_headers()
    app_name = settings.fly_sandbox_app

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{FLY_API_BASE}/apps/{app_name}/machines/{machine_id}",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 404:
                return "stopped"
            resp.raise_for_status()
            data = resp.json()
            return data.get("state", "unknown")
        except Exception:
            logger.exception(f"Failed to get status for Fly machine {machine_id}")
            return "unknown"


async def _wait_for_state(
    machine_id: str,
    target_state: str,
    *,
    timeout: int = 60,
    poll_interval: float = 2.0,
) -> None:
    """Poll machine state until it reaches the target state.

    Args:
        machine_id: The Fly Machine ID.
        target_state: State to wait for (e.g. "started", "stopped").
        timeout: Maximum seconds to wait.
        poll_interval: Seconds between polls.

    Raises:
        TimeoutError: If the machine does not reach the target state in time.
    """
    headers = _fly_headers()
    app_name = settings.fly_sandbox_app
    elapsed = 0.0

    async with httpx.AsyncClient() as client:
        while elapsed < timeout:
            try:
                resp = await client.get(
                    f"{FLY_API_BASE}/apps/{app_name}/machines/{machine_id}",
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code == 404:
                    if target_state in ("stopped", "destroyed"):
                        return
                    raise TimeoutError(
                        f"Machine {machine_id} disappeared while waiting "
                        f"for state '{target_state}'"
                    )
                resp.raise_for_status()
                data = resp.json()
                current_state = data.get("state", "unknown")

                if current_state == target_state:
                    logger.debug(
                        f"Fly machine {machine_id} reached state '{target_state}' "
                        f"after {elapsed:.1f}s"
                    )
                    return

                # If the machine has failed or been destroyed unexpectedly, bail out
                if current_state in ("destroyed", "failed"):
                    raise TimeoutError(
                        f"Machine {machine_id} entered terminal state "
                        f"'{current_state}' while waiting for '{target_state}'"
                    )

            except httpx.HTTPError:
                logger.warning(
                    f"HTTP error polling Fly machine {machine_id}, retrying..."
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

    raise TimeoutError(
        f"Fly machine {machine_id} did not reach state '{target_state}' "
        f"within {timeout}s"
    )
