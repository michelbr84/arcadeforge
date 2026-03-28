"""Unified LLM client for game code generation.

Supports OpenAI, Anthropic, and OpenRouter (OpenAI-compatible).
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("arcadeforge.llm")

SYSTEM_PROMPT = (
    "You are an expert Python game developer specializing in Pygame-CE.\n"
    "Generate a complete, working pygame-ce game based on the user's request.\n\n"
    "REQUIREMENTS:\n"
    "- Use only pygame-ce (import pygame), random, math, sys — no other imports\n"
    "- Window size: 800x600\n"
    "- Must include a proper game loop with event handling\n"
    "- Must handle pygame.QUIT and ESC key to exit cleanly\n"
    "- Must call pygame.quit() and sys.exit() at the end\n"
    "- Include a score display using pygame.font\n"
    "- Include a game over condition with restart option\n"
    "- Game must be fun and playable with smooth controls\n"
    "- Use colors and shapes creatively for visual appeal\n"
    "- Output ONLY the Python code — no markdown fences, no explanations\n"
    "- The code must be a single main.py file, fully self-contained\n"
    "- Target 60 FPS using pygame.time.Clock\n"
)


@dataclass
class LLMConfig:
    provider: str   # "openai", "anthropic", "openrouter"
    api_key: str    # decrypted plaintext key
    model: str      # e.g. "gpt-4o", "claude-sonnet-4-20250514"


async def generate_game_code(
    config: LLMConfig,
    genre: str,
    title: str,
    prompt: str,
    difficulty: str = "medium",
) -> str:
    """Call the LLM to generate pygame code.

    Returns the game code as a string.
    Raises RuntimeError on failure.
    """
    user_message = (
        f"Create a {genre} game called '{title}'.\n"
        f"Difficulty: {difficulty}\n"
        f"Description: {prompt}\n\n"
        f"Generate the complete Python/Pygame-CE code."
    )

    try:
        if config.provider == "anthropic":
            return await _call_anthropic(config, user_message)
        elif config.provider in ("openai", "openrouter"):
            return await _call_openai_compatible(config, user_message)
        else:
            raise ValueError(f"Unknown LLM provider: {config.provider}")
    except Exception as e:
        logger.exception(f"LLM generation failed ({config.provider}/{config.model})")
        raise RuntimeError(f"LLM generation failed: {e}") from e


async def _call_anthropic(config: LLMConfig, user_message: str) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=config.api_key)
    response = await client.messages.create(
        model=config.model or "claude-sonnet-4-20250514",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return _clean_code(response.content[0].text)


async def _call_openai_compatible(config: LLMConfig, user_message: str) -> str:
    import openai

    kwargs: dict = {"api_key": config.api_key}
    if config.provider == "openrouter":
        kwargs["base_url"] = "https://openrouter.ai/api/v1"

    client = openai.AsyncOpenAI(**kwargs)
    response = await client.chat.completions.create(
        model=config.model or "gpt-4o",
        max_tokens=8192,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return _clean_code(response.choices[0].message.content or "")


def _clean_code(code: str) -> str:
    """Strip markdown fences if the LLM wraps the code."""
    code = code.strip()
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code
