"""Game generation worker (arq).

Picks generation jobs from Redis queue and runs genre_forge
to produce game code + blueprint.

Run with: arq workers.generator.worker.WorkerSettings
"""

import sys
from pathlib import Path

# Add workers/ to path so shared_settings is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared_settings import get_redis_settings


async def generate_game_task(ctx: dict, game_id: str) -> dict:
    """Generate a game from prompt + genre using genre_forge engine."""
    # TODO: Phase 4 — implement generation pipeline
    return {"game_id": game_id, "status": "stub"}


class WorkerSettings:
    """arq worker settings."""

    functions = [generate_game_task]
    redis_settings = get_redis_settings()
