"""Genre catalog for ArcadeForge.

Defines available game genres with metadata for the creation form.
In the future, this will read from genre_forge's genre_catalog.md
and per-genre specs.
"""

from pydantic import BaseModel


class Genre(BaseModel):
    id: str
    name: str
    description: str
    difficulty_options: list[str]
    icon: str


# MVP genres (matches infinity-arcade's puzzle, shooter, sports)
GENRE_CATALOG: list[Genre] = [
    Genre(
        id="shooter",
        name="Space Shooter",
        description="Classic top-down space shooter with enemies, projectiles, and score tracking.",
        difficulty_options=["easy", "medium", "hard"],
        icon="rocket",
    ),
    Genre(
        id="puzzle",
        name="Puzzle",
        description="Logic-based puzzle game with increasing difficulty levels.",
        difficulty_options=["easy", "medium", "hard"],
        icon="puzzle",
    ),
    Genre(
        id="sports",
        name="Sports",
        description="Simple sports game (e.g., Pong, breakout) with physics and scoring.",
        difficulty_options=["easy", "medium", "hard"],
        icon="trophy",
    ),
    Genre(
        id="platformer",
        name="Platformer",
        description="Side-scrolling platformer with jumping, obstacles, and collectibles.",
        difficulty_options=["easy", "medium", "hard"],
        icon="gamepad",
    ),
]

GENRE_MAP: dict[str, Genre] = {g.id: g for g in GENRE_CATALOG}


def get_all_genres() -> list[Genre]:
    return GENRE_CATALOG


def get_genre(genre_id: str) -> Genre | None:
    return GENRE_MAP.get(genre_id)
