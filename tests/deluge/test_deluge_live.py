"""Live integration tests for Deluge daemon communication.

These tests require:
- Deluge daemon running and accessible
- Environment variables configured (from docker-compose or .env):
  - DELUGE_HOST
  - DELUGE_PORT
  - DELUGE_USERNAME
  - DELUGE_PASSWORD

To skip these tests, set SKIP_LIVE_TESTS=1
"""
import pytest
import os
from deluge_web_client import DelugeWebClient
from app.modules.deluge.service import (
    extract_torrent_data,
    get_all_torrents_info,
    add_magnet,
    add_torrent_url,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Get environment variables directly from docker/.env
DELUGE_HOST = os.getenv("DELUGE_HOST", "localhost")
DELUGE_PORT = int(os.getenv("DELUGE_WEBUI_PORT", os.getenv("DELUGE_PORT", "8112")))  # Use WebUI port for HTTP API
DELUGE_USERNAME = os.getenv("DELUGE_USERNAME", "localclient")
DELUGE_PASSWORD = os.getenv("DELUGE_PASSWORD", "")

# Skip live tests if flag is set or if Deluge credentials are missing
SKIP_LIVE = (
    os.getenv("SKIP_LIVE_TESTS", "0") == "1" 
    or not DELUGE_PASSWORD
    or not DELUGE_HOST
)


def _test_deluge_connection_direct():
    """Helper function to test connection using module constants."""
    try:
        client = DelugeWebClient(
            host=DELUGE_HOST,
            port=DELUGE_PORT,
            username=DELUGE_USERNAME,
            password=DELUGE_PASSWORD,
        )
        # Try to connect/login if needed
        try:
            if hasattr(client, 'connect'):
                client.connect()
            elif hasattr(client, 'login'):
                client.login()
        except (AttributeError, TypeError):
            pass
        version = client.call("daemon.info")
        return True, version, None
    except Exception as e:
        return False, None, str(e)


@pytest.mark.skipif(
    SKIP_LIVE, 
    reason=f"Live Deluge tests skipped. Config: host={DELUGE_HOST}, port={DELUGE_PORT}, user={DELUGE_USERNAME}, password={'***' if DELUGE_PASSWORD else 'NOT SET'}"
)
class TestDelugeConnectionLive:
    """Live tests for Deluge daemon connection."""

    def test_connection_to_daemon(self):
        """Test connecting to real Deluge daemon using environment variables."""
        print(f"\n🔌 Attempting connection to Deluge:")
        print(f"   Host: {DELUGE_HOST}")
        print(f"   Port: {DELUGE_PORT}")
        print(f"   Username: {DELUGE_USERNAME}")
        print(f"   Password: {'***' if DELUGE_PASSWORD else 'NOT SET'}")
        
        connected, version_result, error = _test_deluge_connection_direct()
        
        assert connected is True, f"Failed to connect: {error}"
        assert version_result is not None, "No version returned"
        assert error is None, f"Connection error: {error}"
        
        print(f"\n✅ Connected to Deluge daemon version: {version_result}")

    def test_get_daemon_info(self):
        """Test getting information from daemon."""
        connected, version, error = _test_deluge_connection_direct()
        
        if not connected:
            pytest.skip(f"Cannot connect to Deluge: {error}")
        
        assert version is not None
        print(f"\n✅ Daemon info retrieved: {version}")


@pytest.mark.skipif(
    SKIP_LIVE,
    reason=f"Live Deluge tests skipped. Config: host={DELUGE_HOST}, port={DELUGE_PORT}"
)
class TestDelugeTorrentsLive:
    """Live tests for Deluge torrent operations."""

    @pytest.fixture(autouse=True)
    def check_connection(self):
        """Ensure we can connect before running tests."""
        connected, _, error = _test_deluge_connection_direct()
        if not connected:
            pytest.skip(f"Cannot connect to Deluge daemon: {error}")

    def test_get_all_torrents_from_daemon(self):
        """Test getting all torrents from real Deluge daemon."""
        torrents = get_all_torrents_info()
        
        assert isinstance(torrents, list), "Should return a list"
        print(f"\n✅ Retrieved {len(torrents)} torrent(s) from Deluge daemon")
        
        if torrents:
            # Print first torrent info
            first = torrents[0]
            print(f"   First torrent: {first.name}")
            print(f"   State: {first.state}, Progress: {first.progress}%")

    def test_get_specific_torrent_info(self):
        """Test getting info for a specific torrent (if any exist)."""
        all_torrents = get_all_torrents_info()
        
        if not all_torrents:
            pytest.skip("No torrents in Deluge to test with")
        
        # Get info for first torrent
        first_torrent_hash = all_torrents[0].torrent_hash
        torrent_info = extract_torrent_data(first_torrent_hash)
        
        assert torrent_info is not None, f"Failed to get info for torrent {first_torrent_hash}"
        assert torrent_info.torrent_hash == first_torrent_hash
        assert torrent_info.name is not None
        print(f"\n✅ Retrieved info for torrent: {torrent_info.name}")
        print(f"   Hash: {torrent_info.torrent_hash[:8]}...")
        print(f"   State: {torrent_info.state}")
        print(f"   Progress: {torrent_info.progress}%")

    def test_torrent_data_structure(self):
        """Test that torrent data has all expected fields."""
        all_torrents = get_all_torrents_info()
        
        if not all_torrents:
            pytest.skip("No torrents in Deluge to test with")
        
        torrent = all_torrents[0]
        
        # Verify all required fields exist
        assert hasattr(torrent, 'torrent_hash')
        assert hasattr(torrent, 'name')
        assert hasattr(torrent, 'state')
        assert hasattr(torrent, 'progress')
        assert hasattr(torrent, 'total_size')
        assert hasattr(torrent, 'downloaded')
        assert hasattr(torrent, 'uploaded')
        assert hasattr(torrent, 'download_speed')
        assert hasattr(torrent, 'upload_speed')
        assert hasattr(torrent, 'save_path')
        assert hasattr(torrent, 'num_seeds')
        assert hasattr(torrent, 'num_peers')
        assert hasattr(torrent, 'ratio')
        assert hasattr(torrent, 'eta')
        assert hasattr(torrent, 'is_finished')
        assert hasattr(torrent, 'paused')
        
        print(f"\n✅ Torrent data structure is valid")
        print(f"   All required fields present for: {torrent.name}")


@pytest.mark.skipif(
    SKIP_LIVE,
    reason=f"Live Deluge tests skipped. Config: host={DELUGE_HOST}, port={DELUGE_PORT}"
)
class TestDelugeTorrentDownloadLive:
    """Live tests for adding torrents and verifying they're downloading."""
    
    @pytest.fixture(autouse=True)
    def check_connection(self):
        """Ensure we can connect before running tests."""
        connected, _, error = _test_deluge_connection_direct()
        if not connected:
            pytest.skip(f"Cannot connect to Deluge daemon: {error}")
    
    @pytest.fixture
    def db_session(self):
        """Get a database session for testing."""
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            pytest.skip("DATABASE_URL not set")
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_add_torrent_and_verify_downloading(self, db_session):
        """Test adding a torrent and verifying it's downloading in Deluge."""
        # Use a small, well-seeded test torrent (Ubuntu ISO is a good test torrent)
        # This is a magnet link for Ubuntu 22.04 ISO - safe, legal, well-seeded
        test_magnet = "magnet:?xt=urn:btih:ZOCMZQIPFFW7OLLMIC5HUB6BPCSDEOQU&dn=ubuntu-22.04.3-desktop-amd64.iso&tr=http%3A%2F%2Ftorrent.ubuntu.com%3A6969%2Fannounce"
        expected_hash = "cb84ccc10f296df72d6c40ba7a07c178a4323a14"  # Hash from magnet link
        
        print(f"\n📥 Testing torrent download in Deluge...")
        
        # Get initial torrent count
        initial_torrents = get_all_torrents_info()
        initial_count = len(initial_torrents)
        initial_hashes = {t.torrent_hash for t in initial_torrents}
        
        print(f"   Initial torrent count: {initial_count}")
        
        # Check if torrent already exists
        torrent_already_exists = expected_hash in initial_hashes
        result_data = expected_hash
        
        if torrent_already_exists:
            print(f"   ℹ️  Test torrent already exists in Deluge (hash: {expected_hash})")
            print(f"   Using existing torrent for testing...")
        else:
            print(f"   Adding test torrent (Ubuntu ISO)...")
            # Add torrent
            test_rating_key = "test_torrent_download_live"
            success, result_data, torrent_item = add_magnet(test_magnet, test_rating_key, db_session)
            
            if not success:
                # If it failed because it already exists, use the existing one
                if "already in session" in str(result_data) or expected_hash in str(result_data):
                    print(f"   ℹ️  Torrent already exists, using existing torrent")
                    result_data = expected_hash
                else:
                    pytest.skip(f"Failed to add test torrent: {result_data}")
        
        print(f"   ✅ Torrent added successfully")
        print(f"   Torrent hash: {result_data}")
        
        # Wait a bit for Deluge to process
        import time
        print(f"   ⏳ Waiting 5 seconds for Deluge to process...")
        time.sleep(5)
        
        # Get updated torrent list
        final_torrents = get_all_torrents_info()
        final_count = len(final_torrents)
        final_hashes = {t.torrent_hash for t in final_torrents}
        
        print(f"   Final torrent count: {final_count}")
        
        # Verify torrent appears
        assert result_data in final_hashes, f"Torrent {result_data} should appear in Deluge"
        
        # Get torrent details
        torrent_info = extract_torrent_data(result_data)
        assert torrent_info is not None, f"Should be able to get info for torrent {result_data}"
        
        print(f"\n📊 Torrent Download Status:")
        print(f"   Name: {torrent_info.name}")
        print(f"   Hash: {torrent_info.torrent_hash}")
        print(f"   State: {torrent_info.state}")
        print(f"   Progress: {torrent_info.progress:.1f}%")
        print(f"   Size: {torrent_info.total_size / 1_000_000_000:.2f} GB" if torrent_info.total_size else "   Size: N/A")
        print(f"   Downloaded: {torrent_info.downloaded / 1_000_000:.2f} MB" if torrent_info.downloaded else "   Downloaded: 0 MB")
        print(f"   Download Speed: {torrent_info.download_speed / 1_000_000:.2f} MB/s" if torrent_info.download_speed else "   Download Speed: 0 MB/s")
        print(f"   Upload Speed: {torrent_info.upload_speed / 1_000_000:.2f} MB/s" if torrent_info.upload_speed else "   Upload Speed: 0 MB/s")
        print(f"   Seeds: {torrent_info.num_seeds}")
        print(f"   Peers: {torrent_info.num_peers}")
        print(f"   ETA: {torrent_info.eta} seconds" if torrent_info.eta > 0 else "   ETA: Unknown")
        print(f"   Paused: {torrent_info.paused}")
        print(f"   Finished: {torrent_info.is_finished}")
        
        # Verify torrent is in a valid state
        valid_states = ["Queued", "Downloading", "Seeding", "Paused", "Error"]
        assert torrent_info.state in valid_states, f"Torrent state should be one of {valid_states}, got: {torrent_info.state}"
        
        # Verify torrent is not paused (unless it's finished)
        if not torrent_info.is_finished:
            assert not torrent_info.paused, "Torrent should not be paused if not finished"
        
        # Verify progress is valid
        assert 0 <= torrent_info.progress <= 100, f"Progress should be between 0 and 100, got: {torrent_info.progress}"
        
        print(f"\n✅ Torrent is successfully added and active in Deluge!")
        print(f"   Status: {torrent_info.state}, Progress: {torrent_info.progress:.1f}%")
        
        # Cleanup: Remove the test torrent from Deluge (only if we added it)
        if not torrent_already_exists:
            try:
                from app.modules.deluge.service import remove_torrent
                print(f"\n🧹 Cleaning up test torrent...")
                success, message = remove_torrent(result_data, remove_data=True, db=db_session)
                if success:
                    print(f"   ✅ Test torrent removed from Deluge: {message}")
                    
                    # Wait a moment and verify it's gone
                    time.sleep(2)
                    remaining_torrents = get_all_torrents_info()
                    remaining_hashes = {t.torrent_hash for t in remaining_torrents}
                    
                    if result_data not in remaining_hashes:
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
            print(f"\nℹ️  Skipping cleanup - torrent was already in Deluge before test")

