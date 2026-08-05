"""Compatibility tests for legacy and canonical database locations."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from src.database import (
    create_database_engine,
    normalize_database_url,
    run_migrations,
)


def _column_names(engine, table: str) -> set[str]:
    with engine.connect() as connection:
        return {
            row[1]
            for row in connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
        }


def _create_legacy_database(path: Path):
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE feedback_items ("
            "id INTEGER PRIMARY KEY, content_hash TEXT NOT NULL UNIQUE, "
            "platform TEXT NOT NULL, content TEXT NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE feedback_analyses ("
            "id INTEGER PRIMARY KEY, feedback_item_id INTEGER NOT NULL UNIQUE, "
            "sentiment TEXT NOT NULL DEFAULT 'unknown')"
        )
        connection.exec_driver_sql(
            "CREATE TABLE human_reviews ("
            "id INTEGER PRIMARY KEY, feedback_item_id INTEGER NOT NULL UNIQUE, "
            "review_status TEXT NOT NULL DEFAULT 'pending')"
        )
        connection.exec_driver_sql(
            "INSERT INTO feedback_items (id, content_hash, platform, content) "
            "VALUES (1, 'legacy-hash', 'legacy', 'preserve me')"
        )
        connection.exec_driver_sql(
            "INSERT INTO feedback_analyses (id, feedback_item_id, sentiment) "
            "VALUES (1, 1, 'negative')"
        )
    return engine


def test_memory_database_url_is_not_converted_to_a_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert normalize_database_url("sqlite:///:memory:") == "sqlite:///:memory:"

    engine = create_database_engine("sqlite:///:memory:")
    run_migrations(engine)

    assert "feedback_type" in _column_names(engine, "feedback_analyses")
    assert not (tmp_path / ":memory:").exists()


def test_relative_legacy_path_is_anchored_to_project_root(tmp_path, monkeypatch):
    project_root = tmp_path / "application"
    other_cwd = tmp_path / "launcher"
    project_root.mkdir()
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)

    normalized = normalize_database_url(
        "sqlite:///data/social_monitor.db", project_root=project_root
    )

    assert normalized == f"sqlite:///{project_root / 'data' / 'social_monitor.db'}"
    assert "launcher" not in normalized


def test_absolute_database_path_is_preserved(tmp_path):
    path = tmp_path / "existing.sqlite3"
    assert normalize_database_url(f"sqlite:///{path}") == f"sqlite:///{path}"


def test_empty_database_upgrade_is_idempotent(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'empty.db'}")

    first = run_migrations(engine)
    second = run_migrations(engine)

    # A new database is created directly at the current schema, so no ALTER
    # operations are needed.  Both invocations still exercise the same public
    # migration entry point used for legacy databases.
    assert first == ()
    assert second == ()
    assert "feedback_type" in _column_names(engine, "feedback_analyses")


def test_existing_legacy_database_upgrades_without_losing_rows(tmp_path):
    engine = _create_legacy_database(tmp_path / "legacy.db")

    run_migrations(engine)
    run_migrations(engine)

    assert {
        "feedback_type",
        "requires_action",
        "action_priority",
        "action_status",
    }.issubset(_column_names(engine, "feedback_analyses"))
    assert {
        "corrected_feedback_type",
        "corrected_requires_action",
        "corrected_action_priority",
        "corrected_action_status",
    }.issubset(_column_names(engine, "human_reviews"))
    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT platform, content FROM feedback_items WHERE id = 1"
        ).one()
    assert tuple(row) == ("legacy", "preserve me")


def test_failed_migration_is_reported_and_not_marked_successful(tmp_path, monkeypatch):
    import src.database as database

    engine = _create_legacy_database(tmp_path / "broken.db")
    monkeypatch.setattr(
        database,
        "_V020_MIGRATIONS",
        (("feedback_analyses", "invalid", "THIS IS NOT VALID SQL"),),
    )

    with pytest.raises(SQLAlchemyError):
        database.run_migrations(engine)

    assert "invalid" not in _column_names(engine, "feedback_analyses")
