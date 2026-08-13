import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, get_db
from app.main import app
from app.models import Case, ChannelEnum, StateEnum, User

_TABLES_TO_CLEAN = [
    "outbound_queue",
    "llm_calls",
    "offers",
    "messages",
    "payments",
    "opt_ins",
    "login_codes",
    "user_memory",
    "cases",
    "users",
    "waitlist_signups",
]


@pytest.fixture
def new_case() -> Case:
    """A fresh, unpersisted Case sitting in the initial 'discovery' state."""
    return Case(
        channel=ChannelEnum.whatsapp,
        counterparty_contact="+15555550123",
        counterparty_name="Test Counterparty",
        state=StateEnum.discovery,
    )


@pytest.fixture
def db_session():
    """A real DB session, truncated clean after the test.

    Application code (AnthropicSubagentClient, the review endpoints) calls
    session.commit() internally, so a rollback-only transactional fixture
    doesn't isolate tests here — instead every test gets a plain session
    against the real DB and we TRUNCATE the app tables at teardown.

    Requires a reachable Postgres matching DATABASE_URL (see .env.example).
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        with engine.begin() as conn:
            for table in _TABLES_TO_CLEAN:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))


@pytest.fixture
def api_client(db_session: Session):
    """A TestClient whose requests run against `db_session` (truncated clean after the test)."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_case(db_session: Session):
    """Factory for a persisted Case, committed to `db_session`."""

    def _make(**overrides) -> Case:
        defaults = dict(
            channel=ChannelEnum.whatsapp,
            vertical="kira-bae",
            counterparty_contact="+15555550123",
            counterparty_name="Test Counterparty",
            state=StateEnum.discovery,
        )
        defaults.update(overrides)
        case = Case(**defaults)
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    return _make


@pytest.fixture
def make_user(db_session: Session):
    """Factory for a persisted User, committed to `db_session`."""

    def _make(**overrides) -> User:
        defaults = dict(phone="+15555550199")
        defaults.update(overrides)
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make
