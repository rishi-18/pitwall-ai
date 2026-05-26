import structlog

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)

from slowapi import (
    Limiter,
    _rate_limit_exceeded_handler
)

from slowapi.util import (
    get_remote_address
)

from slowapi.errors import (
    RateLimitExceeded
)

from prometheus_fastapi_instrumentator import (
    Instrumentator
)

from modules.api.src.routes import (
    sessions,
    predictions,
    rag,
    standings,
    auth,
)

from shared.utils.db import init_db

from shared.utils.redis import (
    get_redis,
    close_redis,
)

log = structlog.get_logger()

limiter = Limiter(
    key_func=get_remote_address
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    log.info("startup_begin")

    init_db()

    await get_redis()

    log.info("startup_complete")

    yield

    await close_redis()

    log.info("shutdown_complete")


app = FastAPI(
    title="PitWall AI",
    description="F1 intelligence platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics"
)

app.include_router(
    auth.router,
    prefix="/v1/auth",
    tags=["Auth"]
)

app.include_router(
    sessions.router,
    prefix="/v1/sessions",
    tags=["Sessions"]
)

app.include_router(
    predictions.router,
    prefix="/v1/predictions",
    tags=["Predictions"]
)

app.include_router(
    rag.router,
    prefix="/v1/rag",
    tags=["RAG"]
)

app.include_router(
    standings.router,
    prefix="/v1/standings",
    tags=["Standings"]
)


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }


@app.get("/ready")
async def ready():

    redis = await get_redis()

    await redis.ping()

    return {
        "status": "ready",
        "db": "ok",
        "redis": "ok",
    }
