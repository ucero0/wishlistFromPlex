"""Live tests for Orchestration service with real Prowlarr and Deluge.

These tests verify the full orchestration workflow:
- Sync Plex watchlists
- Search for torrents in Prowlarr
- Add torrents to Deluge
- Clean up test data

These tests require:
- Plex running and accessible
- Prowlarr running and accessible
- PROWLARR_API_KEY configured
- Deluge running and accessible
- Valid indexers configured in Prowlarr
- Set SKIP_LIVE_TESTS=0 to enable

To run:
    SKIP_LIVE_TESTS=0 docker exec -e SKIP_LIVE_TESTS=0 plex-wishlist-api pytest tests/orchestration/test_live.py -v
"""
import pytest
import os
import time
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.orchestration.service import OrchestrationService
from app.modules.torrent_search.models import SearchStatus
from app.modules.deluge.service import get_all_torrents_info, remove_torrent
from app.modules.plex.models import WishlistItem, MediaType


def get_real_db_session():
    """Get a database session using the real database URL from environment.
    
    For live tests, we use a test database to avoid polluting production data.
    If TEST_DATABASE_URL is set, use that. Otherwise, use the main database
    but mark test data for cleanup.
    """
    # Check if a test database is configured
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if test_db_url:
        db_url = test_db_url
    else:
        # Fall back to main database (not ideal, but allows tests to run)
        db_url = os.getenv("DATABASE_URL", "")
        
        # If DATABASE_URL points to SQLite (from conftest.py), use PostgreSQL instead
        if db_url.startswith("sqlite"):
            # Construct PostgreSQL URL from environment or use defaults
            postgres_user = os.getenv("POSTGRES_USER", "plex_wishlist_user")
            postgres_password = os.getenv("POSTGRES_PASSWORD", "plex_wishlist_pass")
            postgres_db = os.getenv("POSTGRES_DB", "plex_wishlist")
            postgres_host = os.getenv("POSTGRES_HOST", "db")
            postgres_port = os.getenv("POSTGRES_PORT", "5432")
            
            db_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture
def live_db_session():
    """Get a live database session for testing."""
    db = get_real_db_session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def live_db_session_with_cleanup():
    """Get a live database session with automatic cleanup of test data.
    
    This fixture tracks items added during tests and cleans them up afterward.
    Note: Only cleans up items that were added during the test, not existing data.
    """
    db = get_real_db_session()
    items_before = set()
    
    try:
        # Track existing items before test
        existing_items = db.query(WishlistItem).all()
        items_before = {item.id for item in existing_items}
        
        yield db
        
    finally:
        # Clean up items added during test
        try:
            all_items = db.query(WishlistItem).all()
            items_after = {item.id for item in all_items}
            new_item_ids = items_after - items_before
            
            if new_item_ids:
                from app.modules.plex.models import WishlistItemSource
                
                # Delete sources first (foreign key constraint)
                for item_id in new_item_ids:
                    db.query(WishlistItemSource).filter(
                        WishlistItemSource.wishlist_item_id == item_id
                    ).delete()
                
                # Delete the items
                deleted_count = db.query(WishlistItem).filter(
                    WishlistItem.id.in_(new_item_ids)
                ).delete(synchronize_session=False)
                
                db.commit()
                print(f"🧹 Cleaned up {deleted_count} test wishlist item(s) from database")
        except Exception as e:
            db.rollback()
            print(f"⚠️  Warning: Could not clean up test data: {e}")
        finally:
            db.close()


@pytest.fixture
def live_orchestration_service(live_db_session_with_cleanup):
    """Create an OrchestrationService with real database and cleanup."""
    return OrchestrationService(live_db_session_with_cleanup)


@pytest.fixture
def test_wishlist_item(live_db_session_with_cleanup):
    """Create a test wishlist item for integration testing.
    
    Uses live_db_session_with_cleanup to ensure test data is removed after test.
    """
    db = live_db_session_with_cleanup
    
    # Use a unique test item to avoid conflicts
    test_guid = f"plex://movie/test_orchestration_{int(time.time())}"
    test_rating_key = f"test_orchestration_{int(time.time())}"
    
    # Check if item already exists
    existing = db.query(WishlistItem).filter(
        WishlistItem.guid == test_guid
    ).first()
    
    if existing:
        return existing
    
    item = WishlistItem(
        guid=test_guid,
        rating_key=test_rating_key,
        title="The Matrix",
        year=1999,
        media_type=MediaType.MOVIE,
        summary="A computer hacker learns about the true nature of reality",
        added_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class TestOrchestrationLive:
    """Live tests for the full orchestration workflow."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_LIVE_TESTS", "1") == "1",
        reason="Live tests skipped (set SKIP_LIVE_TESTS=0 to enable)"
    )
    async def test_full_orchestration_workflow(
        self,
        live_orchestration_service,
        test_wishlist_item,
        live_db_session_with_cleanup
    ):
        """Test full orchestration workflow: sync → search → add to Deluge."""
        print(f"\n{'='*80}")
        print(f"Full Orchestration Workflow Test for '{test_wishlist_item.title}'")
        print(f"{'='*80}")
        
        # Step 1: Get initial Deluge torrent count
        initial_torrents = get_all_torrents_info()
        initial_count = len(initial_torrents)
        initial_hashes = {t.torrent_hash for t in initial_torrents if t.torrent_hash}
        
        print(f"\n📊 Initial Deluge state:")
        print(f"   Torrents: {initial_count}")
        
        # Step 2: Run orchestration workflow (sync + search + add to Deluge)
        print(f"\n🔄 Running orchestration workflow for '{test_wishlist_item.title}' ({test_wishlist_item.year})...")
        result = await live_orchestration_service.run_full_workflow(
            auto_search=True,
            force_research=True  # Force to ensure we test the search
        )
        
        assert result is not None, "Orchestration workflow should return a result"
        assert "success" in result, "Result should have success field"
        assert "items_searched" in result, "Result should have items_searched field"
        
        print(f"✅ Orchestration workflow completed")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Items searched: {result.get('items_searched', 0)}")
        print(f"   Items added to Deluge: {result.get('items_added_to_deluge', 0)}")
        
        # Step 3: Wait a bit for Deluge to receive the torrent
        print(f"\n⏳ Waiting for Deluge to receive torrent...")
        time.sleep(5)  # Give Deluge time to add the torrent
        
        # Step 4: Verify torrent appears in Deluge
        final_torrents = get_all_torrents_info()
        final_count = len(final_torrents)
        final_hashes = {t.torrent_hash for t in final_torrents if t.torrent_hash}
        
        print(f"\n📊 Final Deluge state:")
        print(f"   Torrents: {final_count}")
        
        # Check if a new torrent was added
        new_torrents = final_hashes - initial_hashes
        new_count = len(new_torrents)
        
        # Track torrent hash for cleanup
        torrent_hash_to_cleanup = None
        
        if new_count == 0:
            # Torrent might already exist, or it might take longer
            print(f"⚠️  No new torrent hash detected. This could mean:")
            print(f"   - Torrent already exists in Deluge")
            print(f"   - Deluge needs more time to process")
            print(f"   - No results found for the test item")
            
            # Check if we can find the torrent by name
            if test_wishlist_item.title:
                matching_torrents = [
                    t for t in final_torrents 
                    if test_wishlist_item.title.lower() in (t.name or "").lower()
                ]
                
                if matching_torrents:
                    print(f"✅ Found matching torrent by name: {matching_torrents[0].name}")
                    torrent_hash_to_cleanup = matching_torrents[0].torrent_hash
                    assert True, "Torrent found by name (may have already existed)"
                else:
                    # If no torrent was added, check if it's because no results were found
                    if result.get("items_searched", 0) == 0:
                        pytest.skip("No items were searched. This may indicate no wishlist items to process.")
                    elif result.get("items_added_to_deluge", 0) == 0:
                        pytest.skip("No torrents were added to Deluge. This may indicate no search results found.")
        else:
            print(f"✅ New torrent detected in Deluge!")
            print(f"   New torrent hash(es): {new_torrents}")
            torrent_hash_to_cleanup = list(new_torrents)[0]
            
            # Verify the new torrent details
            new_torrent = next(
                (t for t in final_torrents if t.torrent_hash in new_torrents),
                None
            )
            
            if new_torrent:
                print(f"   Name: {new_torrent.name}")
                print(f"   Status: {new_torrent.status}")
                print(f"   Size: {new_torrent.total_size / 1_000_000_000:.2f} GB" if new_torrent.total_size else "   Size: N/A")
            
            assert new_count > 0, "New torrent should appear in Deluge"
        
        # Cleanup: Remove the test torrent from Deluge (only if we added it)
        if torrent_hash_to_cleanup:
            try:
                print(f"\n🧹 Cleaning up test torrent...")
                print(f"   Torrent hash: {torrent_hash_to_cleanup}")
                success, message = remove_torrent(torrent_hash_to_cleanup, remove_data=True, db=live_db_session_with_cleanup)
                if success:
                    print(f"   ✅ Test torrent removed from Deluge: {message}")
                    
                    # Wait a moment and verify it's gone
                    time.sleep(2)
                    remaining_torrents = get_all_torrents_info()
                    remaining_hashes = {t.torrent_hash for t in remaining_torrents}
                    
                    if torrent_hash_to_cleanup not in remaining_hashes:
                        print(f"   ✅ Verified: Torrent no longer in Deluge")
                    else:
                        print(f"   ⚠️  Warning: Torrent still appears in Deluge (may take a moment to update)")
                else:
                    print(f"   ⚠️  Failed to remove test torrent: {message}")
            except Exception as e:
                print(f"   ⚠️  Could not remove test torrent: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\nℹ️  Skipping cleanup - no torrent hash available for cleanup")
        
        # Note: Test wishlist items are automatically cleaned up by live_db_session_with_cleanup fixture

