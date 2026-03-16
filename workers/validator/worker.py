"""Game validation worker (arq).

Picks validation jobs from Redis queue and runs
SmokeChecker + GameRunner headless.

Run with: arq workers.validator.worker.WorkerSettings
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared_settings import get_redis_settings


async def validate_game_task(ctx: dict, game_version_id: str) -> dict:
    """Validate a game version: static scan + smoke check + headless run."""
    # TODO: Phase 5 — implement validation pipeline
    return {"game_version_id": game_version_id, "status": "stub"}


class WorkerSettings:
    """arq worker settings."""

    functions = [validate_game_task]
    redis_settings = get_redis_settings()
