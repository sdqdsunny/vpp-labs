"""
Database connection and session management for VPP Phase 2 Simulation Framework.

Provides SQLAlchemy engine, session factory, and connection pooling configuration.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from typing import Generator
import logging
import os

from config import config

logger = logging.getLogger(__name__)


# Create engine with connection pooling
# Use StaticPool for in-memory SQLite in tests
if config.ENV == "testing":
    engine = create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=config.DEBUG,
    )
else:
    engine = create_engine(
        config.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=config.DATABASE_POOL_SIZE,
        max_overflow=config.DATABASE_MAX_OVERFLOW,
        pool_timeout=config.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before using
        echo=config.DEBUG,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance."""
    if "sqlite" in config.DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection.

    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from models.base import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_db() -> None:
    """Drop all database tables (for testing)."""
    from models.base import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()


def close_session(session: Session) -> None:
    """Close a database session."""
    if session:
        session.close()
