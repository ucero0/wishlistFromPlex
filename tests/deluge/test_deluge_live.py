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
from deluge_client import DelugeRPCClient
from app.modules.deluge.service import (
    extract_torrent_data,
    get_all_torrents_info,
)

# Get environment variables directly from docker/.env
DELUGE_HOST = os.getenv("DELUGE_HOST", "localhost")
DELUGE_PORT = int(os.getenv("DELUGE_PORT", "58846"))
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
        client = DelugeRPCClient(
            host=DELUGE_HOST,
            port=DELUGE_PORT,
            username=DELUGE_USERNAME,
            password=DELUGE_PASSWORD,
        )
        client.connect()
        version = client.call("daemon.info")
        client.disconnect()
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

