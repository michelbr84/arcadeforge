"""Tests for game generation, workspace persistence, and versioning."""

import pytest

from app.games.generator import GenerationResult, generate_game, save_to_workspace


def test_generate_shooter():
    """generate_game produces valid shooter code."""
    result = generate_game("shooter", "My Shooter", "A space game", "medium")
    assert isinstance(result, GenerationResult)
    assert result.entrypoint == "main.py"
    assert "main.py" in result.files
    assert "pygame" in result.files["main.py"]
    assert "My Shooter" in result.files["main.py"]
    assert result.metadata["genre"] == "shooter"


def test_generate_puzzle():
    """generate_game produces valid puzzle code."""
    result = generate_game("puzzle", "Block Puzzle", "A color matching game", "easy")
    assert "main.py" in result.files
    assert "grid" in result.files["main.py"].lower()


def test_generate_sports():
    """generate_game produces valid sports/pong code."""
    result = generate_game("sports", "Pong", "Classic pong", "hard")
    assert "paddle" in result.files["main.py"].lower()


def test_generate_platformer():
    """generate_game produces valid platformer code."""
    result = generate_game("platformer", "Jump Game", "A jumping game", "medium")
    assert "JUMP" in result.files["main.py"]


def test_generate_unknown_genre():
    """generate_game raises ValueError for unknown genre."""
    with pytest.raises(ValueError, match="No template for genre"):
        generate_game("mmorpg", "Bad Game", "This should fail", "medium")


def test_generate_difficulty_affects_output():
    """Different difficulties produce different game parameters."""
    easy = generate_game("shooter", "Easy", "test prompt here", "easy")
    hard = generate_game("shooter", "Hard", "test prompt here", "hard")
    assert easy.files["main.py"] != hard.files["main.py"]


def test_save_to_workspace(tmp_path):
    """save_to_workspace writes files atomically."""
    import app.config as config_mod
    original = config_mod.settings.storage_local_path
    config_mod.settings.storage_local_path = str(tmp_path)

    try:
        result = generate_game("shooter", "Test", "A test game prompt", "medium")
        path = save_to_workspace("user123", "game456", 0, result)

        from pathlib import Path
        ws = Path(path)
        assert ws.exists()
        assert (ws / "main.py").exists()
        assert (ws / "blueprint.json").exists()

        import json
        blueprint = json.loads((ws / "blueprint.json").read_text())
        assert blueprint["genre"] == "shooter"
        assert blueprint["entrypoint"] == "main.py"
    finally:
        config_mod.settings.storage_local_path = original


def test_generation_result_metadata():
    """GenerationResult metadata has required fields."""
    result = generate_game("shooter", "Meta Test", "Testing metadata fields", "medium")
    assert "genre" in result.metadata
    assert "title" in result.metadata
    assert "entrypoint" in result.metadata
    assert "controls" in result.metadata
    assert result.summary != ""
