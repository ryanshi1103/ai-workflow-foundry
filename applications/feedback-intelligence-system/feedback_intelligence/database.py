"""SQLAlchemy database engine, sessions, and idempotent schema migrations."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from feedback_intelligence.config import APP_DB_URL, PROJECT_ROOT

logger = logging.getLogger(__name__)


def normalize_database_url(database_url: str, project_root: Path = PROJECT_ROOT) -> str:
    """Anchor relative SQLite URLs while preserving memory and absolute URLs.

    Historically ``sqlite:///data/social_monitor.db`` was interpreted relative
    to the caller's working directory.  Anchoring it to the application root
    prevents an accidental empty database when the launcher is invoked from a
    different directory.  The legacy filename and environment variable remain
    unchanged.
    """

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    database_path = database_url[len(prefix) :]
    if database_path == ":memory:" or database_path.startswith("file:"):
        return database_url

    path = Path(database_path).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return f"{prefix}{path.resolve()}"


def create_database_engine(
    database_url: str = APP_DB_URL,
    project_root: Path = PROJECT_ROOT,
) -> Engine:
    """Create an engine with the application's SQLite safety settings."""

    normalized_url = normalize_database_url(database_url, project_root)
    target_engine = create_engine(
        normalized_url,
        echo=False,
        connect_args={"check_same_thread": False} if normalized_url.startswith("sqlite") else {},
        pool_pre_ping=True,
    )

    if normalized_url.startswith("sqlite"):

        @event.listens_for(target_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            # SQLite memory databases cannot persist WAL files and report
            # ``memory`` mode.  Requesting WAL remains safe for file databases.
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return target_engine


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    """Return a new database session. Caller is responsible for closing it."""

    return SessionLocal()


def init_db(target_engine: Engine = engine) -> None:
    """Create all current tables without changing existing user rows."""

    from feedback_intelligence.models import Base

    Base.metadata.create_all(bind=target_engine)


_V020_MIGRATIONS = (
    ("feedback_analyses", "feedback_type", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("feedback_analyses", "requires_action", "BOOLEAN NOT NULL DEFAULT 0"),
    ("feedback_analyses", "action_priority", "TEXT"),
    ("feedback_analyses", "action_status", "TEXT NOT NULL DEFAULT 'new'"),
    ("human_reviews", "corrected_feedback_type", "TEXT"),
    ("human_reviews", "corrected_requires_action", "BOOLEAN"),
    ("human_reviews", "corrected_action_priority", "TEXT"),
    ("human_reviews", "corrected_action_status", "TEXT"),
)


def run_migrations(target_engine: Engine = engine) -> tuple[str, ...]:
    """Upgrade an empty or existing database and return applied operations.

    Migrations are additive, idempotent, and run in a transaction.  Exceptions
    are deliberately propagated so callers never mistake a partial upgrade for
    success.  Existing tables and rows are not dropped or rewritten.
    """

    init_db(target_engine)
    applied: list[str] = []

    with target_engine.begin() as connection:
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")

        for table, column, column_definition in _V020_MIGRATIONS:
            columns = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            }
            if column in columns:
                continue
            connection.exec_driver_sql(
                f"ALTER TABLE {table} ADD COLUMN {column} {column_definition}"
            )
            operation = f"{table}.{column}"
            applied.append(operation)
            logger.info("Migration added %s", operation)

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_feedback_analyses_feedback_type "
            "ON feedback_analyses (feedback_type)"
        )

    logger.info("Migrations complete (%d applied)", len(applied))
    return tuple(applied)
