import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.auth.sessions import close_redis
from app.config import settings
from app.games.arcade_router import router as arcade_router
from app.games.router import router as games_router
from app.jobs.queue import close_queue
from app.pages.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # Start background tasks
    from app.games.reaper import reaper_loop

    reaper_task = asyncio.create_task(reaper_loop())

    yield

    # Shutdown: cancel background tasks and close connections
    reaper_task.cancel()
    try:
        await reaper_task
    except asyncio.CancelledError:
        pass

    await close_queue()
    await close_redis()


app = FastAPI(
    title="ArcadeForge API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(arcade_router)
app.include_router(games_router)
app.include_router(users_router)


@app.get("/api/health")
async def health():
    """Health check endpoint. Returns service status."""
    return {
        "status": "ok",
        "service": "arcadeforge-api",
        "version": "0.1.0",
    }
