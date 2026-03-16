"""Sandbox lifecycle worker (arq).

Manages game play session containers:
spin up, monitor TTL, clean up.
"""


async def start_sandbox_task(ctx: dict, play_session_id: str) -> dict:
    """Start a sandbox container for a play session."""
    # TODO: Phase 6 — implement sandbox orchestration
    return {"play_session_id": play_session_id, "status": "stub"}


async def cleanup_sandbox_task(ctx: dict, sandbox_ref: str) -> dict:
    """Clean up an expired or stopped sandbox container."""
    # TODO: Phase 6 — implement cleanup
    return {"sandbox_ref": sandbox_ref, "status": "stub"}


class WorkerSettings:
    """arq worker settings."""

    functions = [start_sandbox_task, cleanup_sandbox_task]
    redis_settings = None  # configured from env in Phase 1.3
