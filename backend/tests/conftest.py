"""Pytest setup: integration tests run against a separate PostgreSQL database.

The app's DATABASE_URL is overridden with TEST_DATABASE_URL *before* the app is
imported, so the normal development database can never be touched by tests.
"""
import os

from sqlalchemy.engine import make_url

from app.config import get_settings

_test_url = get_settings().test_database_url
if not _test_url or not (make_url(_test_url).database or "").endswith("_test"):
    raise RuntimeError("Set TEST_DATABASE_URL to a database whose name ends in '_test'.")
os.environ["DATABASE_URL"] = _test_url
get_settings.cache_clear()

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import BACKEND_DIR  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.utils.security import create_access_token, hash_password  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    """Build the schema from the real Alembic migrations (this also tests them)."""
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    """Empty every table after each test so tests stay independent."""
    yield
    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def make_user(db, email: str, role: UserRole = UserRole.CUSTOMER, name: str = "Test User") -> User:
    user = User(full_name=name, email=email, password_hash=hash_password(PASSWORD), role=role)
    db.add(user)
    db.commit()
    return user


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


@pytest.fixture
def customer(db) -> User:
    return make_user(db, "customer@example.com", name="Casey Customer")


@pytest.fixture
def admin(db) -> User:
    return make_user(db, "admin@example.com", UserRole.ADMIN, name="Alex Admin")


@pytest.fixture
def customer_headers(customer) -> dict[str, str]:
    return auth_headers(customer)


@pytest.fixture
def admin_headers(admin) -> dict[str, str]:
    return auth_headers(admin)
