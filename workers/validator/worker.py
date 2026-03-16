"""Game validation worker (arq).

Picks validation jobs from Redis queue and runs
SmokeChecker + GameRunner headless.
"""


async def validate_game_task(ctx: dict, game_version_id: str) -> dict:
    """Validate a game version: static scan + smoke check + headless run."""
    # TODO: Phase 5 — implement validation pipeline
    return {"game_version_id": game_version_id, "status": "stub"}


class WorkerSettings:
    """arq worker settings."""

    functions = [validate_game_task]
    redis_settings = None  # configured from env in Phase 1.3
