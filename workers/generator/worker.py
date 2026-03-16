"""Game generation worker (arq).

Picks generation jobs from Redis queue and runs genre_forge
to produce game code + blueprint.
"""


async def generate_game_task(ctx: dict, game_id: str) -> dict:
    """Generate a game from prompt + genre using genre_forge engine."""
    # TODO: Phase 4 — implement generation pipeline
    return {"game_id": game_id, "status": "stub"}


class WorkerSettings:
    """arq worker settings."""

    functions = [generate_game_task]
    redis_settings = None  # configured from env in Phase 1.3
