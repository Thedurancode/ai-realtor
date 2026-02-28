"""Shared test fixtures for the RealtorClaw test suite.

Uses a file-based SQLite database so tests are fast, isolated,
and require no external services.
"""

import os

# Force SQLite before any app imports touch the database module.
os.environ["DATABASE_URL"] = "sqlite:///test.db"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.database import Base, get_db
# Import all models so SQLAlchemy registers every relationship/table.
import app.models  # noqa: F401
from app.models.agent import Agent
from app.models.property import Property, PropertyStatus, PropertyType, DealType
from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.models.offer import Offer, OfferStatus, FinancingType
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.deal_type_config import DealTypeConfig
from app.auth import hash_api_key


# ---------------------------------------------------------------------------
# Database engine & session
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all tables between tests for clean isolation."""
    yield
    # After each test, delete all rows from every table in reverse dependency order
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def db():
    """Yield a database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """FastAPI TestClient wired to the test database session.

    Because the ApiKeyMiddleware creates its own SessionLocal() session,
    we patch SessionLocal in app.main to use our test engine so the
    middleware sees the same data as the test fixtures.
    """
    from app.main import app
    import app.main as main_module

    # Override get_db so routers use the test db session
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Also patch SessionLocal used by the ApiKeyMiddleware
    original_session_local = main_module.SessionLocal
    main_module.SessionLocal = TestingSessionLocal

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    main_module.SessionLocal = original_session_local


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

TEST_API_KEY = "sk_live_test_key_for_unit_tests_only"


@pytest.fixture()
def agent(db) -> Agent:
    """Create and return a test agent with a known API key."""
    a = Agent(
        name="Test Agent",
        email="test@example.com",
        phone="555-0100",
        license_number="LIC-001",
        api_key_hash=hash_api_key(TEST_API_KEY),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture()
def agent_headers() -> dict:
    """Auth headers using the test API key."""
    return {"x-api-key": TEST_API_KEY}


@pytest.fixture()
def second_agent(db) -> Agent:
    """Create a second agent for multi-agent tests."""
    a = Agent(
        name="Second Agent",
        email="second@example.com",
        phone="555-0200",
        license_number="LIC-002",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture()
def sample_property(db, agent) -> Property:
    """Create and return a sample property."""
    p = Property(
        title="123 Test St",
        address="123 Test Street",
        city="Testville",
        state="NJ",
        zip_code="07001",
        price=350000.0,
        bedrooms=3,
        bathrooms=2.0,
        square_feet=1800,
        lot_size=0.25,
        year_built=1990,
        property_type=PropertyType.HOUSE,
        status=PropertyStatus.NEW_PROPERTY,
        agent_id=agent.id,
        pipeline_status="pending",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def second_property(db, agent) -> Property:
    """Create a second property for multi-property tests."""
    p = Property(
        title="456 Oak Ave",
        address="456 Oak Avenue",
        city="Testburg",
        state="NY",
        zip_code="10001",
        price=500000.0,
        bedrooms=4,
        bathrooms=3.0,
        square_feet=2500,
        property_type=PropertyType.HOUSE,
        status=PropertyStatus.NEW_PROPERTY,
        agent_id=agent.id,
        pipeline_status="pending",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def sample_contact(db, sample_property) -> Contact:
    """Create and return a sample contact (lawyer)."""
    c = Contact(
        property_id=sample_property.id,
        name="John Doe",
        first_name="John",
        last_name="Doe",
        role=ContactRole.LAWYER,
        phone="555-0101",
        email="john@example.com",
        company="Doe Law Firm",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture()
def buyer_contact(db, sample_property) -> Contact:
    """Create a buyer contact."""
    c = Contact(
        property_id=sample_property.id,
        name="Jane Buyer",
        first_name="Jane",
        last_name="Buyer",
        role=ContactRole.BUYER,
        phone="555-0102",
        email="jane@example.com",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture()
def sample_contract(db, sample_property) -> Contract:
    """Create and return a sample contract."""
    c = Contract(
        property_id=sample_property.id,
        name="Purchase Agreement",
        description="Standard purchase agreement",
        status=ContractStatus.DRAFT,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture()
def sample_todo(db, sample_property) -> Todo:
    """Create and return a sample todo."""
    t = Todo(
        property_id=sample_property.id,
        title="Schedule inspection",
        description="Call inspector to schedule",
        status=TodoStatus.PENDING,
        priority=TodoPriority.HIGH,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def sample_offer(db, sample_property) -> Offer:
    """Create and return a sample offer."""
    o = Offer(
        property_id=sample_property.id,
        offer_price=325000.0,
        earnest_money=5000.0,
        financing_type=FinancingType.CASH,
        closing_days=30,
        status=OfferStatus.SUBMITTED,
        is_our_offer=True,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture()
def sample_notification(db) -> Notification:
    """Create and return a sample notification."""
    n = Notification(
        type=NotificationType.GENERAL,
        priority=NotificationPriority.MEDIUM,
        title="Test Notification",
        message="This is a test notification",
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n
