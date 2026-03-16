"""Game validation worker (arq).

Picks validation jobs from Redis queue and runs
smoke checks on the generated game code.

Run with: arq workers.validator.worker.WorkerSettings
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps" / "api"))

from shared_settings import get_redis_settings

logger = logging.getLogger("arcadeforge.validator")


async def validate_game_task(ctx: dict, validation_run_id: str) -> dict:
    """Validate a game version.

    1. Load validation run + game version from DB
    2. Run structural smoke checks on source code
    3. Save report
    4. Mark validation as completed (passed/failed)
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.models import GameVersion, ValidationRun

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Load validation run
            result = await session.execute(
                select(ValidationRun).where(ValidationRun.id == validation_run_id)
            )
            run = result.scalar_one_or_none()
            if run is None:
                logger.error(f"ValidationRun {validation_run_id} not found")
                return {"validation_run_id": validation_run_id, "status": "error"}

            # Load game version
            ver_result = await session.execute(
                select(GameVersion).where(GameVersion.id == run.game_version_id)
            )
            version = ver_result.scalar_one_or_none()
            if version is None:
                run.status = "failed"
                run.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"validation_run_id": validation_run_id, "status": "error"}

            logger.info(f"Validating game version {version.game_id} v{version.version}")

            # Smoke checks
            checks_passed = True
            findings = []

            code = version.source_code or ""

            # Check 1: Has pygame import
            if "import pygame" not in code:
                findings.append("Missing pygame import")
                checks_passed = False

            # Check 2: Has main loop
            if "while" not in code and "for" not in code:
                findings.append("No game loop detected")
                checks_passed = False

            # Check 3: Has quit handler
            if "pygame.QUIT" not in code and "QUIT" not in code:
                findings.append("No QUIT event handler")
                checks_passed = False

            # Check 4: Has display update
            if "pygame.display.flip" not in code and "pygame.display.update" not in code:
                findings.append("No display update call")
                checks_passed = False

            # Check 5: Has ESC key handler
            if "K_ESCAPE" not in code and "pygame.K_ESCAPE" not in code:
                findings.append("No ESC key handler")

            # Check 6: Minimum code length
            if len(code) < 100:
                findings.append("Code is too short (< 100 chars)")
                checks_passed = False

            # Update validation run
            run.status = "passed" if checks_passed else "failed"
            run.completed_at = datetime.now(timezone.utc)
            # Store findings as a simple report path (future: save to file)
            if findings:
                run.report_json_path = f"findings: {'; '.join(findings)}"

            await session.commit()

            logger.info(
                f"Validation {validation_run_id}: {'passed' if checks_passed else 'failed'} "
                f"({len(findings)} findings)"
            )
            return {
                "validation_run_id": validation_run_id,
                "status": run.status,
                "findings": findings,
            }

    except Exception as e:
        logger.exception(f"Failed to validate {validation_run_id}")
        try:
            async with session_factory() as session:
                result = await session.execute(
                    select(ValidationRun).where(ValidationRun.id == validation_run_id)
                )
                run = result.scalar_one_or_none()
                if run:
                    run.status = "failed"
                    run.completed_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception:
            pass
        return {"validation_run_id": validation_run_id, "status": "error", "message": str(e)}
    finally:
        await engine.dispose()


class WorkerSettings:
    """arq worker settings."""

    functions = [validate_game_task]
    redis_settings = get_redis_settings()
