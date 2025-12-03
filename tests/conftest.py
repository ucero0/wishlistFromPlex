"""Pytest configuration and fixtures."""
import pytest
import os
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test environment variables BEFORE importing app modules
# These MUST be set for tests to work consistently
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_KEY"] = "test-api-key-12345"
os.environ["PLEX_SYNC_INTERVAL_HOURS"] = "6"
os.environ["LOG_LEVEL"] = "DEBUG"
# Deluge env vars use setdefault to allow live tests to use real Docker env vars

from app.core.db import Base, get_db
from app.main import app
from app.modules.plex.models import PlexUser, WishlistItem, WishlistItemSource, MediaType
from app.modules.deluge.models import TorrentItem, TorrentStatus


# Test database engine (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_key_header() -> dict:
    """Return headers with valid API key."""
    return {"X-API-Key": "test-api-key-12345"}


@pytest.fixture
def sample_user(db_session: Session) -> PlexUser:
    """Create a sample Plex user for testing."""
    user = PlexUser(
        name="TestUser",
        plex_token="test-token-abc123xyz",
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_inactive_user(db_session: Session) -> PlexUser:
    """Create an inactive Plex user for testing."""
    user = PlexUser(
        name="InactiveUser",
        plex_token="inactive-token-xyz",
        active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_wishlist_item(db_session: Session) -> WishlistItem:
    """Create a sample wishlist item for testing."""
    item = WishlistItem(
        guid="plex://movie/5d776825880197001ec90a21",
        rating_key="12345",
        title="Inception",
        year=2010,
        media_type=MediaType.MOVIE,
        summary="A skilled thief is offered a chance to have his past crimes forgiven.",
        thumb="/library/metadata/12345/thumb",
        art="/library/metadata/12345/art",
        content_rating="PG-13",
        studio="Warner Bros.",
        added_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def sample_wishlist_item_with_source(
    db_session: Session, 
    sample_user: PlexUser,
    sample_wishlist_item: WishlistItem
) -> WishlistItem:
    """Create a wishlist item with an associated source."""
    source = WishlistItemSource(
        wishlist_item_id=sample_wishlist_item.id,
        plex_user_id=sample_user.id,
        first_added_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(sample_wishlist_item)
    return sample_wishlist_item


@pytest.fixture
def multiple_wishlist_items(db_session: Session) -> list:
    """Create multiple wishlist items for testing."""
    items = [
        WishlistItem(
            guid="plex://movie/test1",
            rating_key="1001",
            title="The Matrix",
            year=1999,
            media_type=MediaType.MOVIE,
            summary="A computer hacker discovers reality is a simulation.",
        ),
        WishlistItem(
            guid="plex://movie/test2",
            rating_key="1002",
            title="The Matrix Reloaded",
            year=2003,
            media_type=MediaType.MOVIE,
            summary="Neo and the rebels fight against the machines.",
        ),
        WishlistItem(
            guid="plex://show/test3",
            rating_key="1003",
            title="Breaking Bad",
            year=2008,
            media_type=MediaType.SHOW,
            summary="A chemistry teacher turns to making drugs.",
        ),
        WishlistItem(
            guid="plex://movie/test4",
            rating_key="1004",
            title="Interstellar",
            year=2014,
            media_type=MediaType.MOVIE,
            summary="Explorers travel through a wormhole in space.",
        ),
    ]
    
    for item in items:
        item.added_at = datetime.now(timezone.utc)
        item.last_seen_at = datetime.now(timezone.utc)
        db_session.add(item)
    
    db_session.commit()
    
    for item in items:
        db_session.refresh(item)
    
    return items


@pytest.fixture
def mock_plex_item():
    """Create a mock Plex API item."""
    mock_item = MagicMock()
    mock_item.guid = "plex://movie/mock123"
    mock_item.ratingKey = "99999"
    mock_item.title = "Mock Movie"
    mock_item.year = 2024
    mock_item.type = "movie"
    mock_item.summary = "A mock movie for testing."
    mock_item.thumb = "/library/metadata/99999/thumb"
    mock_item.art = "/library/metadata/99999/art"
    mock_item.contentRating = "R"
    mock_item.studio = "Mock Studios"
    return mock_item


@pytest.fixture
def mock_plex_account(mock_plex_item):
    """Create a mock Plex account."""
    mock_account = MagicMock()
    mock_account.username = "testuser"
    mock_account.email = "test@example.com"
    mock_account.title = "Test User"
    mock_account.uuid = "uuid-12345"
    mock_account.watchlist.return_value = [mock_plex_item]
    mock_account.searchDiscover.return_value = [mock_plex_item]
    return mock_account
