"""Shared test fixtures."""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure tests run in mock mode with no real API calls
os.environ["APP_MOCK_MODE"] = "true"
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ["APIFY_TOKEN"] = ""
os.environ["APP_DB_URL"] = "sqlite:///:memory:"
os.environ["APP_LOG_LEVEL"] = "WARNING"


@pytest.fixture(autouse=True)
def clean_config():
    """Reload config for each test with test environment."""
    import importlib

    import src.config

    importlib.reload(src.config)
    yield


@pytest.fixture
def db_engine():
    """Create a fresh in-memory SQLite database for each test."""

    # Force memory DB
    engine = create_engine("sqlite:///:memory:", echo=False)
    from src.models import Base

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(bind=db_engine)  # noqa: N806 — sqlalchemy naming convention
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
