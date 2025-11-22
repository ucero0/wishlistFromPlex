import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.core.db import Base, get_db
from app.core.config import Settings, settings
from app.main import app


# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Override settings for testing
    with patch.object(settings, 'api_key', 'test-api-key'):
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Test settings with test values."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        api_key="test-api-key",
        plex_sync_interval_hours=1,
        log_level="DEBUG",
    )


@pytest.fixture
def sample_plex_token():
    """Sample Plex token for testing."""
    return "test-plex-token-12345"


@pytest.fixture
def sample_plex_user_data():
    """Sample Plex user data for testing."""
    return {
        "name": "Test User",
        "token": "test-plex-token-12345",
    }


@pytest.fixture
def sample_wishlist_item_data():
    """Sample wishlist item data for testing."""
    return {
        "uid": "plex://movie/guid/tmdb://12345",
        "title": "Test Movie",
        "year": 2023,
    }

