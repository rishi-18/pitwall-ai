"""Database connection utilities â€” shared across API, ingestion, and ML modules."""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from shared.models.base import Base


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pitwall:pitwall_secret@localhost:5432/pitwall"
)

ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)


# Async engine â€” FastAPI usage
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


# Sync engine â€” ingestion + Celery usage
sync_engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)


async def get_async_db() -> AsyncSession:
    """FastAPI dependency for DB sessions."""
    async with AsyncSessionLocal() as session:
        yield session


def create_hypertable(
    table_name: str,
    time_column: str = "timestamp"
) -> None:
    """Convert a Postgres table into a TimescaleDB hypertable."""

    with sync_engine.connect() as conn:
        conn.execute(
            text(
                f"""
                SELECT create_hypertable(
                    '{table_name}',
                    '{time_column}',
                    if_not_exists => TRUE
                );
                """
            )
        )

        conn.commit()


def init_db() -> None:
    """Create all tables and set up hypertables."""
    # Import models so SQLAlchemy registers them before create_all
    from shared.models import telemetry  # noqa: F401
    Base.metadata.create_all(sync_engine)
    # Hypertable must be created AFTER the table exists
    try:
        create_hypertable("telemetry", "timestamp")
    except Exception as e:
        import structlog
        log = structlog.get_logger()
        log.warning("hypertable_setup_skipped", error=str(e))