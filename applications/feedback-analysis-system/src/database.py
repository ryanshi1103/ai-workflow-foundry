"""SQLAlchemy database engine and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.config import APP_DB_URL

# Normalize relative SQLite path to absolute
_db_url = APP_DB_URL
if _db_url.startswith("sqlite:///"):
    from pathlib import Path

    rel = _db_url[len("sqlite:///"):]
    _db_url = f"sqlite:///{Path(rel).resolve()}"

engine = create_engine(
    _db_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
    if "sqlite" in str(engine.url):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Session:
    """Return a new database session. Caller is responsible for closing."""
    return SessionLocal()


def init_db():
    """Create all tables if they don't exist."""
    from src.models import Base

    Base.metadata.create_all(bind=engine)


def run_migrations():
    """Run idempotent SQLite migrations to add new columns safely.

    Each migration checks whether the column already exists before adding it,
    so repeated calls are safe and won't corrupt existing data.
    """
    import logging

    logger = logging.getLogger(__name__)

    # Ensure WAL mode is set
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")

    # ── Migration: v0.2.0 — feedback type & action tracking ─────
    _v020_migrations = [
        # FeedbackAnalysis new columns
        ("feedback_analyses", "feedback_type", "TEXT NOT NULL DEFAULT 'unknown'"),
        ("feedback_analyses", "requires_action", "BOOLEAN NOT NULL DEFAULT 0"),
        ("feedback_analyses", "action_priority", "TEXT"),
        ("feedback_analyses", "action_status", "TEXT NOT NULL DEFAULT 'new'"),
        # HumanReview new columns
        ("human_reviews", "corrected_feedback_type", "TEXT"),
        ("human_reviews", "corrected_requires_action", "BOOLEAN"),
        ("human_reviews", "corrected_action_priority", "TEXT"),
        ("human_reviews", "corrected_action_status", "TEXT"),
    ]

    with engine.connect() as conn:
        for table, column, col_def in _v020_migrations:
            # Check if column exists
            result = conn.exec_driver_sql(
                f"PRAGMA table_info({table})"
            ).fetchall()
            existing_columns = {row[1] for row in result}

            if column not in existing_columns:
                try:
                    conn.exec_driver_sql(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"
                    )
                    logger.info("Migration: added %s.%s (%s)", table, column, col_def)
                except Exception as e:
                    logger.warning("Migration skipped for %s.%s: %s", table, column, e)
            else:
                logger.debug("Migration: column %s.%s already exists, skipping", table, column)

        conn.commit()

    # Create index on feedback_type if not exists
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_feedback_analyses_feedback_type "
                "ON feedback_analyses (feedback_type)"
            )
        except Exception as e:
            logger.debug("Index creation skipped: %s", e)
        conn.commit()

    logger.info("Migrations complete")
