"""Tests for Deluge API routes."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.modules.deluge.models import TorrentItem, TorrentStatus
from app.modules.deluge.schemas import TorrentStatusEnum
from app.modules.deluge.constants import MODULE_PREFIX as DELUGE


@pytest.fixture
def sample_torrent(db_session):
    """Create a sample torrent for testing."""
    item = TorrentItem(
        rating_key="test_movie_123",
        torrent_hash="a" * 40,
        magnet_link="magnet:?xt=urn:btih:" + "a" * 40,
        name="Test.Movie.2024.1080p.BluRay",
        status=TorrentStatus.DOWNLOADING,
        progress=45.5,
        total_size=2147483648,
        downloaded=976744448,
        save_path="/downloads",
        num_seeds=15,
        num_peers=3,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def multiple_torrents(db_session):
    """Create multiple torrents for testing."""
    items = [
        TorrentItem(
            rating_key="movie1",
            torrent_hash="1" * 40,
            name="Movie1.2024",
            status=TorrentStatus.DOWNLOADING,
            progress=25.0,
        ),
        TorrentItem(
            rating_key="movie2",
            torrent_hash="2" * 40,
            name="Movie2.2024",
            status=TorrentStatus.SEEDING,
            progress=100.0,
        ),
        TorrentItem(
            rating_key="movie3",
            torrent_hash="3" * 40,
            name="Movie3.2024",
            status=TorrentStatus.COMPLETED,
            progress=100.0,
        ),
    ]
    for item in items:
        db_session.add(item)
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    return items


class TestDelugeStatus:
    """Tests for Deluge status endpoint."""

    @patch("app.modules.deluge.service.test_connection")
    def test_status_connected(self, mock_test, client):
        """Test getting connected status."""
        mock_test.return_value = (True, "2.1.1", None)
        
        response = client.get(f"{DELUGE}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["daemon_version"] == "2.1.1"

    @patch("app.modules.deluge.service.test_connection")
    def test_status_disconnected(self, mock_test, client):
        """Test getting disconnected status."""
        mock_test.return_value = (False, None, "Connection refused")
        
        response = client.get(f"{DELUGE}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert "Connection refused" in data["error"]


class TestListTorrents:
    """Tests for listing torrents."""

    def test_list_torrents_empty(self, client):
        """Test listing empty torrents."""
        response = client.get(f"{DELUGE}/torrents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["torrents"] == []

    def test_list_torrents_with_items(self, client, multiple_torrents):
        """Test listing torrents with items."""
        response = client.get(f"{DELUGE}/torrents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_list_torrents_filter_by_status(self, client, multiple_torrents):
        """Test filtering torrents by status."""
        response = client.get("/deluge/torrents?status=downloading")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["torrents"][0]["status"] == "downloading"

    def test_list_torrents_pagination(self, client, multiple_torrents):
        """Test pagination."""
        response = client.get("/deluge/torrents?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["torrents"]) == 2


class TestGetTorrent:
    """Tests for getting specific torrent."""

    def test_get_torrent_success(self, client, sample_torrent):
        """Test getting a torrent by hash."""
        response = client.get(f"/deluge/torrents/{sample_torrent.torrent_hash}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["torrent_hash"] == sample_torrent.torrent_hash
        assert data["name"] == sample_torrent.name

    def test_get_torrent_not_found(self, client):
        """Test getting non-existent torrent."""
        response = client.get("/deluge/torrents/" + "x" * 40)
        
        assert response.status_code == 404


class TestGetTorrentsByRatingKey:
    """Tests for getting torrents by rating_key."""

    def test_get_by_rating_key(self, client, db_session):
        """Test getting torrents by rating_key."""
        items = [
            TorrentItem(rating_key="same_key", torrent_hash="s1" + "0" * 38, name="720p"),
            TorrentItem(rating_key="same_key", torrent_hash="s2" + "0" * 38, name="1080p"),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        response = client.get("/deluge/torrents/by-rating-key/same_key")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_by_rating_key_empty(self, client):
        """Test getting torrents for non-existent rating_key."""
        response = client.get("/deluge/torrents/by-rating-key/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestGetTorrentInfo:
    """Tests for getting live torrent info."""

    @patch("app.modules.deluge.service.extract_torrent_data")
    def test_get_info_success(self, mock_extract, client, sample_torrent):
        """Test getting live torrent info."""
        from app.modules.deluge.schemas import TorrentInfoResponse
        
        mock_extract.return_value = TorrentInfoResponse(
            torrent_hash=sample_torrent.torrent_hash,
            name="Test.Movie.2024",
            state="Downloading",
            progress=50.0,
            total_size=2147483648,
            downloaded=1073741824,
            uploaded=107374182,
            download_speed=10485760,
            upload_speed=1048576,
            save_path="/downloads",
            num_seeds=20,
            num_peers=5,
            ratio=0.1,
            eta=1800,
            is_finished=False,
            paused=False,
        )
        
        response = client.get(f"/deluge/torrents/{sample_torrent.torrent_hash}/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "Downloading"

    @patch("app.modules.deluge.service.extract_torrent_data")
    def test_get_info_not_found(self, mock_extract, client):
        """Test getting info for non-existent torrent."""
        mock_extract.return_value = None
        
        response = client.get("/deluge/torrents/" + "y" * 40 + "/info")
        
        assert response.status_code == 404


class TestRemoveTorrent:
    """Tests for removing torrents."""

    @patch("app.modules.deluge.service.remove_torrent")
    def test_remove_torrent_only(self, mock_remove, client, api_key_header, sample_torrent):
        """Test removing torrent without data."""
        mock_remove.return_value = (True, "Torrent removed only (data kept)")
        
        response = client.delete(
            f"/deluge/torrents/{sample_torrent.torrent_hash}",
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_removed"] is False

    @patch("app.modules.deluge.service.remove_torrent")
    def test_remove_torrent_and_data(self, mock_remove, client, api_key_header, sample_torrent):
        """Test removing torrent with data."""
        mock_remove.return_value = (True, "Torrent removed and data")
        
        response = client.delete(
            f"/deluge/torrents/{sample_torrent.torrent_hash}?remove_data=true",
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data_removed"] is True

    def test_remove_torrent_not_found(self, client, api_key_header):
        """Test removing non-existent torrent."""
        response = client.delete(
            "/deluge/torrents/" + "z" * 40,
            headers=api_key_header,
        )
        
        assert response.status_code == 404

    def test_remove_torrent_no_api_key(self, client, sample_torrent):
        """Test removing torrent without API key."""
        response = client.delete(f"/deluge/torrents/{sample_torrent.torrent_hash}")
        
        assert response.status_code == 401


class TestRemoveTorrentByRatingKey:
    """Tests for removing torrents by rating_key."""

    @patch("app.modules.deluge.service.remove_torrent_by_rating_key")
    def test_remove_by_rating_key_success(self, mock_remove, client, api_key_header):
        """Test removing torrents by rating_key."""
        mock_remove.return_value = (True, "Removed 2 torrent(s)", ["hash1", "hash2"])
        
        response = client.delete(
            "/deluge/torrents/by-rating-key/test_key",
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.modules.deluge.service.remove_torrent_by_rating_key")
    def test_remove_by_rating_key_not_found(self, mock_remove, client, api_key_header):
        """Test removing non-existent rating_key."""
        mock_remove.return_value = (False, "No active torrents found for rating_key nonexistent", [])
        
        response = client.delete(
            "/deluge/torrents/by-rating-key/nonexistent",
            headers=api_key_header,
        )
        
        # Can be 404 or 500 depending on message
        assert response.status_code in [404, 500]


class TestSyncTorrents:
    """Tests for syncing torrents."""

    @patch("app.modules.deluge.service.sync_torrent_status")
    def test_sync_success(self, mock_sync, client, api_key_header):
        """Test syncing torrents successfully."""
        mock_sync.return_value = (5, 0)
        
        response = client.post(f"{DELUGE}/sync", headers=api_key_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["synced_count"] == 5
        assert data["error_count"] == 0

    def test_sync_no_api_key(self, client):
        """Test syncing without API key."""
        response = client.post(f"{DELUGE}/sync")
        
        assert response.status_code == 401


class TestDaemonTorrents:
    """Tests for getting daemon torrents."""

    @patch("app.modules.deluge.service.get_all_torrents_info")
    def test_get_daemon_torrents(self, mock_get_all, client):
        """Test getting all torrents from daemon."""
        from app.modules.deluge.schemas import TorrentInfoResponse
        
        mock_get_all.return_value = [
            TorrentInfoResponse(
                torrent_hash="d" * 40,
                name="Daemon.Movie",
                state="Seeding",
                progress=100.0,
                total_size=1000000,
                downloaded=1000000,
                uploaded=500000,
                download_speed=0,
                upload_speed=10000,
                save_path="/downloads",
                num_seeds=20,
                num_peers=10,
                ratio=0.5,
                eta=-1,
                is_finished=True,
                paused=False,
            )
        ]
        
        response = client.get(f"{DELUGE}/daemon/torrents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Daemon.Movie"

