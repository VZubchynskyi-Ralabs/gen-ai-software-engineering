"""
Shared pytest fixtures.
Uses an isolated in-memory SQLite database for each test session via a temp file.
"""
import os
import tempfile
import pytest

from src.app import create_app


@pytest.fixture(scope="session")
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    application = create_app(db_path=db_path, testing=True)
    yield application
    os.unlink(db_path)


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture
def fresh_app():
    """Per-test isolated DB — use for tests that need a clean slate."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    application = create_app(db_path=db_path, testing=True)
    with application.test_client() as c:
        yield c
    os.unlink(db_path)


VALID_TICKET = {
    "customer_id": "CUST-001",
    "customer_email": "test@example.com",
    "customer_name": "Test User",
    "subject": "Test subject line",
    "description": "This is a test description that is long enough to pass validation.",
    "category": "technical_issue",
    "priority": "medium",
    "status": "new",
    "metadata": {
        "source": "api",
        "browser": "Chrome",
        "device_type": "desktop",
    },
    "tags": ["test", "automation"],
}

