"""Seed games from infinity-arcade generated_games into the ArcadeForge database.

Usage: python scripts/seed_games.py

Requires DATABASE_URL env var (Neon connection string).
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# Map infinity-arcade genres to ArcadeForge genres
GENRE_MAP = {
    "shooter": "shooter",
    "puzzle": "puzzle",
    "grid-based-puzzle": "puzzle",
    "sports": "sports",
    "top-down-open-world-action": "platformer",
    "arcade_arena_growth": "platformer",
}


async def main():
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: Set DATABASE_URL env var")
        sys.exit(1)

    # Convert asyncpg URL format
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    games_dir = Path(__file__).parent.parent.parent / "infinity-arcade" / "generated_games"
    if not games_dir.exists():
        print(f"ERROR: {games_dir} not found")
        sys.exit(1)

    conn = await asyncpg.connect(db_url)

    # Get or create a system user for seeded games
    system_user = await conn.fetchrow(
        "SELECT id FROM users WHERE username = $1", "arcadeforge"
    )
    if not system_user:
        user_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO users (id, email, username, password_hash, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, NOW(), NOW())""",
            user_id,
            "system@arcadeforge.app",
            "arcadeforge",
            "$argon2id$v=19$m=65536,t=3,p=4$system_placeholder_not_for_login",
            "active",
        )
        print(f"Created system user: arcadeforge ({user_id})")
    else:
        user_id = system_user["id"]
        print(f"Using existing user: arcadeforge ({user_id})")

    count = 0
    for game_dir in sorted(games_dir.iterdir()):
        if not game_dir.is_dir():
            continue

        game_json_path = game_dir / "game.json"
        main_py_path = game_dir / "main.py"

        if not game_json_path.exists() or not main_py_path.exists():
            print(f"  SKIP {game_dir.name} — missing game.json or main.py")
            continue

        meta = json.loads(game_json_path.read_text(encoding="utf-8"))
        code = main_py_path.read_text(encoding="utf-8")

        title = meta.get("name", game_dir.name)
        raw_genre = meta.get("genre", "platformer")
        genre = GENRE_MAP.get(raw_genre, "platformer")
        pitch = meta.get("pitch", "")[:200]
        prompt = meta.get("pitch", "")

        # Check if game already exists
        existing = await conn.fetchrow(
            "SELECT id FROM games WHERE title = $1 AND owner_user_id = $2",
            title, user_id,
        )
        if existing:
            print(f"  SKIP {title} — already exists")
            continue

        game_id = uuid.uuid4()
        version_id = uuid.uuid4()

        # Insert game
        await conn.execute(
            """INSERT INTO games (id, owner_user_id, genre, title, pitch, prompt,
                                  visibility, play_count, status, status_message,
                                  created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())""",
            game_id, user_id, genre, title, pitch, prompt,
            "public", 0, "ready", f"Imported from infinity-arcade ({raw_genre})",
        )

        # Insert version v0
        blueprint = {
            "genre": genre,
            "title": title,
            "prompt": prompt,
            "difficulty": "medium",
            "entrypoint": "main.py",
            "controls": meta.get("controls", {}),
            "generated_by": "infinity-arcade",
            "original_genre": raw_genre,
        }

        await conn.execute(
            """INSERT INTO game_versions (id, game_id, version, blueprint_json,
                                          source_code, created_at)
               VALUES ($1, $2, $3, $4, $5, NOW())""",
            version_id, game_id, 0, json.dumps(blueprint), code,
        )

        print(f"  OK {title} ({genre}) — {len(code)} chars")
        count += 1

    await conn.close()
    print(f"\nDone! Inserted {count} games into the arcade.")


if __name__ == "__main__":
    asyncio.run(main())
