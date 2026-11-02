"""Shared pytest fixtures for all test modules."""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Ensure backend/app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


def _make_test_engine():
    """Create a fresh in-memory SQLite engine with FK support and StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh test engine per test."""
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a session bound to the test engine."""
    TestingSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """Create a FastAPI test client using the test DB engine.

    The key fix: both the dependency-injected session AND the tables live
    on the same in-memory engine, so the app can actually find the tables.
    """
    TestingSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)

    def _override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_job_data():
    """Sample job creation payload."""
    return {
        "title": "Senior Python Developer",
        "description": (
            "We are looking for a Senior Python Developer with 5+ years of experience "
            "in building scalable web applications using FastAPI or Django. Must have "
            "strong experience with PostgreSQL, Redis, Docker, and AWS. Experience with "
            "machine learning and data pipelines is a plus. BS in Computer Science required."
        ),
    }
